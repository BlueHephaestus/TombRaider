#!/bin/bash
# REMOVE WHEN DONE WITH DEV
#set -x

# Usage: ./tomb_raider [OPTIONS] DISK
# or ./tomb_raider [OPTIONS] --image IMAGEFILE
# Make sure you are in the directory you want your output stored or specify with -d
# THIS MAY TAKE SEVERAL DAYS TO COMPLETE!
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi


# Default arguments
output_dir=$(realpath "./tomb") # Default directory
image_given=0 # Defaults to getting image from drive
keep_image=0 # Defaults to deleting the image after we sort
dryrun=0 # Default, run everything

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
original_dir=$(pwd)
safecopy_dir="$output_dir/safecopy"
testdisk_dir="$output_dir/testdisk"
photorec_dir="$output_dir/photorec"

mkdir -p $output_dir
if [[ $image_given -eq 0 ]]; then
	mkdir -p safecopy_dir
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

# Recover / undelete all filetypes, without filesystem structure. Uses PhotoRec with all usual filetypes enabled.
# There are about 5 that it doesn't enable by default, and if you really want those types of files I recommend
# running it separately. Or just make a PR to add that if you think it should be added :)

# This pretty much always produces some results, even in the cases of randomly wiped drives,
# just because some conditions for files are very lenient, such that they only require 2 byte
# header signatures, for instance.
# we run with these options
#/d directory - output directory
# partition_none - get the entire disk
# everything,enable - all default filetypes
# paranoid - yes (no paranoid misses a lot of files (trading that for speed) , and paranoid bf is only for piecing together images (maybe only jpg) and takes exponentially longer)
# keep corrupted - yes
# expert - no
# lowmem - no

cd $photorec_dir
if [[ $dryrun -eq 0 ]]; then
	photorec /debug /log /d . /cmd $image partition_none,options,keep_corrupted_file,paranoid,fileopt,everything,enable,search
fi


cd $output_dir
# Condense Filesystem - Remove all subdirectories in photorec/ and testdisk/, instead converting
# all filenames into sanitized versions which also contain their original filepath in the filename.
echo "Condensing result Testdisk Filesystem"
python3 $original_dir/condense_filesystem.py $testdisk_dir
echo "Condensing result PhotoRec Filesystem"
python3 $original_dir/condense_filesystem.py $photorec_dir

# Index newly condensed filesystems, mapping filenames to hashes of file contents
echo "Indexing Testdisk Filesystem"
python3 $original_dir/index_filesystem.py $testdisk_dir
echo "Indexing PhotoRec Filesystem"
python3 $original_dir/index_filesystem.py $photorec_dir

# Remove duplicates from both filesystems, using indexes
testdisk_index=$output_dir/testdisk.index
photorec_index=$output_dir/photorec.index
testdisk_n=$(cat $testdisk_index | wc -l)
photorec_n=$(cat $photorec_index | wc -l)

echo "Indexed $testdisk_n files in Testdisk Filesystem"
echo "Indexed $photorec_n files in PhotoRec Filesystem"

echo "Removing Duplicates from Testdisk Filesystem"
python3 $original_dir/remove_indexed_duplicates.py $testdisk_dir $testdisk_index
echo "Removing Duplicates from PhotoRec Filesystem"
python3 $original_dir/remove_indexed_duplicates.py $photorec_dir $photorec_index

fs_partitions=$((`mmls -a $image | wc -l`-5))
new_testdisk_n=$(cat $testdisk_index | wc -l)
new_photorec_n=$(cat $photorec_index | wc -l)
echo "Removed $((testdisk_n-new_testdisk_n)) Duplicate Files from Testdisk Filesystem, \
there are now $new_testdisk_n files in the Testdisk Filesystem"
echo "Removed $((photorec_n-new_photorec_n)) Duplicate Files from PhotoRec Filesystem, \
there are now $new_photorec_n files in the PhotoRec Filesystem"
testdisk_n=new_testdisk_n
photorec_n=new_photorec_n

# Finally merge the two filesystems, in a special way. Here's how. If Testdisk recovered files/data from the image,
# then the files/data it recovered will have filesystem metadata - their filename and location
# of each file. PhotoRec usually does not have any of this data for the files it's recovered, either because
# of how it recovers them, or simply because when a filesystem "deletes" a file, it deletes its pointers and labels
# for the file, i.e. its name and location on the filesystem.
#
# So because of this, if we find a duplicate pair - a file that is in testdisk once and in photorec once, we
# discard the one from photorec since testdisk will have greater than or equal to the metadata that photorec has.
echo "Merging Testdisk and PhotoRec Filesystems and Removing Pair Duplicates"

fs_dir=$output_dir/filesystem/
fs_index=$output_dir/filesystem.index
mkdir -p $fs_dir

python3 $original_dir/merge_testdisk_photorec.py $testdisk_dir $testdisk_index $photorec_dir $photorec_index $fs_dir $fs_index
fs_n=$(cat $fs_index | wc -l)
echo "Removed $(((testdisk_n+photorec_n)-fs_n)) Pair Duplicate Files"
echo "Merged $testdisk_n Testdisk files and $photorec_n PhotoRec files into new Tomb Filesystem with $fs_n files."

# Remove any files in the "known good" hashsets from NIST NSRL.
# We check our indexes for any files in these hashsets, with the knowledge that these are files which were
# either already on the operating system at initialization, or are otherwise common and usual programs we'd
# expect to find on a hard drive, and we don't care about (e.g. Photoshop, Microsoft Word, Minesweeper).
# Of course if they've used those programs and they keep files, we'll still have those, which is a good and bad
# thing, because it means the boring programs may still have files laying around, but it also means that
# we'll still know what data was produced or if they *used* bad programs which were also known.
# Essentially, this removes static non-relevant data
echo "Comparing Tomb Filesystem files to NSRL Known Files and Removing Known files"
nsrl_md5s=$original_dir/nsrl.md5s #md5s because it only has md5s, not an index
python3 $original_dir/remove_known_files.py $fs_index $nsrl_md5s

new_fs_n=$(cat $fs_index | wc -l)
echo "Removed $((fs_n-new_fs_n)) NSRL Known Files from Tomb Filesystem, \
there are now $new_fs_n files in the Tomb Filesystem"
fs_n=new_fs_n

# Do it again on any personal MD5 hashsets we have
echo "Comparing Tomb Filesystem files to HashSets.com Known Files and Removing Known files"
hashsets_md5s=$original_dir/hashsets.md5s #md5s because it only has md5s, not an index
python3 $original_dir/remove_known_files.py $fs_index $hashsets_md5s

new_fs_n=$(cat $fs_index | wc -l)
echo "Removed $((fs_n-new_fs_n)) Hashsets.com Known Files from Tomb Filesystem, \
there are now $new_fs_n files in the Tomb Filesystem"
fs_n=new_fs_n

# Filter remaining files, determining their filetype and using our blacklist file to remove any matching
# extensions and/or classes which we want to disregard.
python3 $original_dir/filter_files

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
