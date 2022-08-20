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

Add option or defualt behavior to create a simulation of the original filesystem using symbolic links
to the actual files, so that the only thing thats created is directories and links
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
delete_image=0 #defaults to not deleting image afterwards
skip_safecopy=0
skip_testdisk=0
skip_photorec=0
skip_raid=0
skip_crypto=0
skip_archive=0

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
		-nf|--no-image-file)
      # To delete the image file after running. Usually to save disk space.
			delete_image=1
			shift # past argument
			;;
		-ns|--no-safecopy)
			# To skip safecopy. Should have a suitable image instead of the safecopy one.
			skip_safecopy=1
			shift # past argument
			;;
		-nt|--no-testdisk)
			# To skip testdisk
			skip_testdisk=1
			shift # past argument
			;;
		-np|--no-photorec)
			# To skip photorec
			skip_photorec=1
			shift # past argument
			;;
		-nr|--no-raid)
			# To skip raiding
			skip_raid=1
			shift # past argument
			;;
		-nc|--no-crypto)
			# To skip crypto salvaging
			skip_crypto=1
			shift # past argument
			;;
		-na|--no-archive)
			# To skip archiving / compressing
			skip_archive=1
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
#TODO -nx TO NOT DO ANYTHING AND JUST VIBE

set -- "${positional_args[@]}" # restore positional parameters

# Print chosen parameters
echo "OUTPUT DIRECTORY     = ${output_dir}"
echo "SKIP SAFECOPY        = ${skip_safecopy}"
echo "SKIP TESTDISK        = ${skip_testdisk}"
echo "SKIP PHOTOREC        = ${skip_photorec}"
echo "SKIP RAIDING         = ${skip_raid}"
echo "SKIP CRYPTO SALVAGE  = ${skip_crypto}"
echo "SKIP ARCHIVING       = ${skip_archive}"
echo "DELETE IMAGE FILE    = ${delete_image}"

# Safecopy / Imaging has strange needed behavior.
# If they want to skip safecopy, we will run assuming that the given arg is the disk to work on
# IF they don't want to skip, we will make the image from whatever they give instead,
# and if it's already a disk image, we will skip making an image entirely.

image_given=0
if [[ -f $1 ]]; then #given arg is a file, assume it's an image file
  image=$1
  image_given=1
	echo "IMAGE FILE           = ${image}"
else
	if [[ -n $1 ]]; then # still is an arg, assume it's a drive specified instead
		drive=$1
		echo "DRIVE                = ${drive}"
	else
    # no args given, break
    echo "You must call Tomb Raider with a disk or image file, none found."
    exit
	fi
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

# Always make these
mkdir -p $output_dir
mkdir -p $safecopy_dir
mkdir -p $testdisk_dir
mkdir -p $photorec_dir


# SAFECOPY - Imaging as much of drive as possible
# From /dev/sdX to disk.img, drive to image
# Will skip if -ns / --no-safecopy is specified, OR if an image file is provided.
if [[ $skip_safecopy -eq 0 && $image_given -eq 0 ]]; then # get an image from the drive, since we don't have one yet
  cd $safecopy_dir
	image=$(realpath "$output_dir/../disk.img") # Default image loc
  echo "Imaging drive $drive to new image $image. DO NOT MOUNT OR UNPLUG YOUR DEVICE."
  safecopy --stage1 $drive $image
  safecopy --stage2 $drive $image
  safecopy --stage3 $drive $image

	echo "Imaging Complete. You may now unplug your device."

else # already have image
  image=$drive
  if [[ $skip_safecopy -eq 1 ]]; then
    echo "Skipping safecopy imaging, using $image for disk interface."
  else
    echo "Disk Image provided, skipping safecopy imaging step. And using $image for disk interface."
  fi
fi
# At this this point $image is the only interface to our source device.

if [[ $skip_testdisk -eq 0 ]]; then # don't skip
  echo "Attempting to obtain Filesystem with Testdisk"
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
    # Tried to find a way for this to show the number of files copied but it isn't in the documentation
    # and doesn't seem to be possible with scripted runs. We don't use /debug since that causes
    # the runs to be far slower.
    testdisk /log /cmd $image advanced,$i,list,filecopy
    ((i++))
  done
fi

if [[ $skip_photorec -eq 0 ]]; then # don't skip
  echo "Recovering / Undeleting files on $image"

  cd $photorec_dir
  photorec /debug /log /d $photorec_dir/photorec /cmd $image partition_none,options,keep_corrupted_file,paranoid,fileopt,everything,enable,search
fi

cd $output_dir

# Raid
if [[ $skip_raid -eq 0 ]]; then #don't skip
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
fi

# Salvage - Check Tomb Filesystem for any indications of cryptocurrency / bitcoin
if [[ $skip_crypto -eq 0 ]]; then #don't skip
  echo "Checking drive for any evidence of cryptocurrency or bitcoin."
  echo "Any filepaths matching rulesets will appear as matches."
  python3 $original_dir/crypto_salvager.py $output_dir
fi

# CLEAN UP
# Delete the image if they specify, keep it otherwise.
if [[ $delete_image -eq 1 ]]; then
	echo "Removing Disk Image $image..."
	rm $image
else
	echo "Keeping Tomb Raider Image $image since not instructed to delete. Use -nf / --no-image-file to delete."
fi

# COMPRESS / ARCHIVE TOMB
# Now that tomb is complete, compress it using TAR + LZ4
# Reasons for this are many:
# 0. Tarfile because it's the way you make a file out of a directory
# 1. GZIP takes hours for even a relatively small tarfile (40GB) whereas lz4 takes less than 10 minutes
# (it takes days for any normal size hard drive)
# 2. Compression ratios are very comparable between them despite this
# 3*. My theory for this is because it's compressing a bunch of files rather than one big file, so block compression
# may be more intuitive here. But this is a semi-reason since i'm not sure how it works under the hood.
#TODO add print statement for how much file size was reduced via compression
# TODO REMOVE TOMB WHEN DONE WITH ARCHIVING AS AN OPTION?

if [[ $skip_archive -eq 0 ]]; then #don't skip
  # Copy the index out of this so we don't need to decompress to view contents
  cp "$output_dir/filesystem.index" $output_dir/..
  echo "Archiving/Compressing Tomb Filesystem to save disk space."
  output_archive=${output_dir%/}.tar.lz4
  tar cf - -C $output_dir/ . | pv -s $(du -sb $output_dir/ | awk '{print $1}') | lz4 > $output_archive
fi

# Return to where this was called
cd $original_dir
echo "Happy Hunting! -Blue"

exit 0
