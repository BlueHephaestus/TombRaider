#!/bin/bash -x
# Usage: ./tomb_raider <DRIVE>
# Make sure you are in the directory you want your output stored.
# THIS MAY TAKE SEVERAL DAYS TO COMPLETE!
DRIVE=${1}
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Safecopy - Imaging as much of drive as possible
echo "Imaging drive $DRIVE to disk.img in current directory. DO NOT MOUNT YOUR DEVICE."
safecopy --stage1 $DRIVE disk.img
safecopy --stage2 $DRIVE disk.img
safecopy --stage3 $DRIVE disk.img
echo "Imaging Complete. You may now unplug your device."

# Scalpel - Carving out parts that match private key hex patterns
echo "Searching through ALL bytes on image for any matching private key patterns."
scalpel disk.img

# Salvage - Check scalpel'd files for any keys that connect to an address with BTC balance.
echo "Trying mutations and various formattings for found keys to check for BTC Balance."
echo "Key Variants will appear as they are tried, and the program will exit with information EARLY if a balance is found. Good luck!"
python3 bitcoin_salvager.py scalpel-output/

echo "Happy Hunting! -Blue"


