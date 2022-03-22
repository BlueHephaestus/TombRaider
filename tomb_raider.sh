#!/bin/bash +x
# REMOVE WHEN DONE WITH DEV

# Usage: ./tomb_raider <DRIVE>
# Make sure you are in the directory you want your output stored.
# THIS MAY TAKE SEVERAL DAYS TO COMPLETE!
drive=${1}
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
# Make output directory
#mkdir -p tombraider_output
#cd tombraider_output


# Safecopy - Imaging as much of drive as possible
# From /dev/sdX to disk.img
echo "Imaging drive $DRIVE to disk.img in current directory. DO NOT MOUNT YOUR DEVICE."
#safecopy --stage1 $DRIVE disk.img
#safecopy --stage2 $DRIVE disk.img
#safecopy --stage3 $DRIVE disk.img
echo "Imaging Complete. You may now unplug your device."

echo "Attempting to obtain Filesystem"
# Get the filesystem on the drive to retain any file metadata and organization, if possible
# MMLS - Get the number of allocated partitions on disk.img, if any (has to be alloc to have filesystem)
# This is what we use to determine an upper bound for how many partitions will have recoverable fs's on testdisk.
# tested via running it on 5 (if not more) of my own salvaged hard disks. This will include any boot files, etc.
# More info in README
fs_partitions=$((`mmls -a disk.img | wc -l`-5))
echo "Found $fs_partitions Possible Filesystem Partitions on disk.img"

i=1
while [[ $i -le $fs_partitions ]]
do
  echo "Running Testdisk to attempt to recover files on partition $i/$fs_partitions"
  testdisk /debug /log /cmd disk.img advanced,$i,list,filecopy
  ((i++))
done





# Scalpel - Carving out parts that match private key hex patterns
echo "Searching through ALL bytes on image for any matching private key patterns."
#scalpel disk.img

# Salvage - Check scalpel'd files for any keys that connect to an address with BTC balance.
echo "Trying mutations and various formattings for found keys to check for BTC Balance."
echo "Key Variants will appear as they are tried, and the program will exit with information EARLY if a balance is found. Good luck!"
#python3 bitcoin_salvager.py scalpel-output/

echo "Happy Hunting! -Blue"


