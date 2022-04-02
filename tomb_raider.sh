#!/bin/bash
# REMOVE WHEN DONE WITH DEV
#set -x

: '
TODO
make sure there is option for no known hashes
option for never remove anything
cache the optimal md5 buffer size once we compute it once
save the .npy file once its obtained
add an option to save all found files for future hashing

'
# Usage: ./tomb_raider [OPTIONS] DISK
# or ./tomb_raider [OPTIONS] --image IMAGEFILE
# Make sure you are in the directory you want your output stored or specify with -d
# THIS MAY TAKE SEVERAL DAYS TO COMPLETE!
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi


# Default arguments
output_dir=$(realpath "./tomb")
image_given=0 # Defaults to getting image from drive
keep_image=0 # Defaults to deleting the image after we sort
dryrun=0 # Default, run everything

#echo "Tomb Raider will now ask for any optional values. Feel free to pass --defaults to use defaults and skip this in the future."
#
#default_output_dir=$(realpath "./tomb")
#read -p "Enter your output dir [$default_output_dir]: " output_dir
#output_dir=${output_dir:-$default_output_dir}
#
#while :
#do
#  read -p "Is your tomb an image file (disk.dd, device.img, asdf.raw, etc) or a disk (/dev/sda, /dev/sdf2, etc)? [image/disk]: " tomb_type
#  if [[ $tomb_type != "disk" && $tomb_type != "image" ]]; then
#    echo "Please choose 'disk' or 'image'"
#  else
#    break
#  fi
#done
#
#read -p "Enter your output dir [$default_output_dir]: " output_dir
#output_dir=${output_dir:-$default_output_dir}


# Parse arguments
positional_args=()
while [[ $# -gt 0 ]]; do
	case $1 in
		-d|--output-dir)
			output_dir=$(realpath $2)
			shift # past argument
			shift # past value
			;;
		-i|--image)
			image_given=1
			image=$(realpath $2)
			shift # past argument
			shift # past value
			;;
		-k|--keep-image)
			# If they want to keep the disk.img file in the case they didn't provide their own (default).
			# Usually tombraider deletes this to save space once the files have been condensed
			keep_image=1
			shift # past argument
			;;
		-n|--dryrun)
			# If we want to avoid calls and just print what would happen.
			dryrun=1
			shift # past argument
			;;
		-*|--*)
			echo "Unknown option $1"
			exit 1
			;;
		*)
			positional_args+=("$1") # save positional arg
			shift # past argument
			;;
  esac
done

set -- "${positional_args[@]}" # restore positional parameters

# Print chosen parameters
echo "OUTPUT DIRECTORY     = ${output_dir}"
echo "DRY RUN              = ${dryrun}"
echo "KEEP TOMB IMAGE FILE = ${keep_image}"
echo "IMAGE FILE PROVIDED  = ${image_given}"
if [[ $image_given -eq 1 ]]; then #image file exists
	echo "IMAGE FILE           = ${image}"
else
	if [[ -n $1 ]]; then # drive specified instead
		drive=$1
		echo "DRIVE                = ${drive}"
	fi
fi

# Neither image nor drive given, break
if [[ $image_given -eq 0 && -z $drive ]]; then
	# TRIGGER USAGE CALL
	echo "You must pass a drive for tomb raider via './tomb_raider /dev/sdX' or an image via './tomb_raider --image disk.img'"
	exit 1
fi

#echo "Number files in SEARCH PATH with EXTENSION:" $(ls -1 "${SEARCHPATH}"/*."${EXTENSION}" | wc -l)

# OUTPUT LAYOUT
# All files will go in the output directory, which is ./tomb/ if not specified. 
# Will not move the image file if one is already given.
# If not given, will use default name of disk.img in output directory.
echo "Preparing output directories."
original_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
safecopy_dir="$output_dir/safecopy"
testdisk_dir="$output_dir/testdisk"
photorec_dir="$output_dir/photorec"
known_md5s="$original_dir/known.npy"

mkdir -p $output_dir
if [[ $image_given -eq 0 ]]; then
	mkdir -p $safecopy_dir
fi
mkdir -p $testdisk_dir
mkdir -p $photorec_dir


# SAFECOPY - Imaging as much of drive as possible
# From /dev/sdX to disk.img
# WILL SKIP IF THE IMAGE FILE IS PROVIDED
cd $safecopy_dir
if [[ $image_given -eq 0 ]]; then # get an image from the drive, since we don't have one yet
	image=$(realpath "$output_dir/disk.img") # Default image loc
	echo "Imaging drive $drive to new image $image. DO NOT MOUNT YOUR DEVICE."

	if [[ $dryrun -eq 0 ]]; then # run them if not dryrunning
		safecopy --stage1 $drive $image
		safecopy --stage2 $drive $image
		safecopy --stage3 $drive $image
	fi

	echo "Imaging Complete. You may now unplug your device."

else # already have image
	echo "Existing image provided, using $image."
fi

echo "Attempting to obtain Filesystem"
# Filesystem directory
cd $testdisk_dir

# Get the filesystem on the drive to retain any file metadata and organization, if possible
# MMLS - Get the number of allocated partitions on disk.img, if any (has to be alloc to have filesystem)
# This is what we use to determine an upper bound for how many partitions will have recoverable fs's on testdisk.
# tested via running it on 5 (if not more) of my own salvaged hard disks. This will include any boot files, etc.
# More info in README
fs_partitions=$((`mmls -a $image | wc -l`-5))
if [[ $fs_partitions -lt 0 ]]; then
	fs_partitions=0
fi
echo "Found $fs_partitions Possible Filesystem Partitions on $image."

i=1
while [[ $i -le $fs_partitions ]]
do
	echo "Running Testdisk to attempt to recover files on partition $i/$fs_partitions"
	if [[ $dryrun -eq 0 ]]; then # run them if not dryrunning
		testdisk /debug /log /cmd $image advanced,$i,list,filecopy
	fi
	((i++))
done

echo "Recovering / Undeleting files on $image"

cd $photorec_dir
if [[ $dryrun -eq 0 ]]; then
	photorec /debug /log /d $photorec_dir/photorec /cmd $image partition_none,options,keep_corrupted_file,paranoid,fileopt,everything,enable,search
fi

cd $output_dir

testdisk_n=$(find $testdisk_dir -type f | wc -l)
photorec_n=$(find $photorec_dir -type f | wc -l)
echo "Testdisk Filesystem Recovered $testdisk_n Files."
echo "PhotoRec Filesystem Recovered $photorec_n Files."
echo "Current Number of Files: $(($testdisk_n + $photorec_n))"
echo "Testdisk and PhotoRec acquired, now Raiding and creating new Tomb Filesystem from recovered data."
echo "This will Process, Condense, Remove Duplicates, and Organize all found files into the Tomb Filesystem."
#echo "Processing, Condensing, Indexing, and removing Duplicates or Known files in Testdisk Filesystem."
python3 $original_dir/raid_filesystem.py $testdisk_dir $photorec_dir $output_dir $known_md5s
tomb_n=$(find $output_dir -type f | wc -l)
condense_perc=$(bc <<<"scale=2;$tomb_n/($testdisk_n+$photorec_n)*100")
echo "Tomb Filesystem Complete. New File Count: $tomb_n. This has been condensed to $condense_perc% of the original size."

# Scalpel - Carving out parts that match private key hex patterns
#echo "Searching through ALL bytes on image for any matching private key patterns."
#scalpel disk.img

# Salvage - Check scalpel'd files for any keys that connect to an address with BTC balance.
#echo "Trying mutations and various formattings for found keys to check for BTC Balance."
#echo "Key Variants will appear as they are tried, and the program will exit with information EARLY if a balance is found. Good luck!"
#python3 bitcoin_salvager.py scalpel-output/

# CLEAN UP
# If they didn't provide an image, then we have a TR Image. We delete it if they don't specify otherwise.
if [[ $image_given -eq 0 && $keep_image -eq 0 ]]; then
	echo "Removing Tomb Raider $image to save disk space."
	rm $image
elif [[ $image_given -eq 0 && $keep_image -eq 1 ]]; then
	echo "Keeping Tomb Raider Image $image since requested by user."
fi


# Return to where this was called
cd $original_dir
echo "Happy Hunting! -Blue"

exit 0
