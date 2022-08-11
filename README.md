# Description

Automated Imaging, Undeletion, Recovery, Indexing, Organizing, Some Forensics, and Crypto Salvaging for any storage device Linux can recognize.

For those who are here from the BSides talk - thank you for coming! I am still updating the build_deps.sh script and the rest of this README, but overall it's still pretty easy to get running as per the instructions below. Thank you!!!

Given any hard drive, Tomb Raider will do everything in its power to recover as much data as possible on the drive, and do so entirely automatically. It was designed because I started wanting to do data recovery on any trashed hard drive I could find, and found myself repeating the same steps over and over for them, or skipping steps because I didn't want to spend the time constantly coming back to it and having to do yet another tedious step for one hard drive after another. I was finding hard drives faster than I could image them, and found myself spending all day doing this and obsessing over it - which wasn't nearly as fun as exploring them and seeing what cool stuff was on them.

And so, TombRaider came to be - a bot to automatically raid these "tombs" - old hard drives or new ones I'd find in hackerspaces or the dump.

# Usage

After installation, simply call the script on the block device matching your disk - viewable with the `lsblk` command. /dev/sda, or /dev/md1 are examples.

This is only supported on Linux at the moment, since all the tools are readily available on Linux as well as interfacing directly with storage devices. Plus i'm lazy.

Unfortunately requires sudo for full disk access. 

```
sudo bash tomb_raider.sh /dev/sdX
```

Aaaaand that's it! It may have higher or lesser requirements for host storage, and it may take hours or days depending on your resources and the specs / size of the storage device you're working with - the specifics of which will be covered in the Walkthrough section - but it's designed so you can just Plug and Play :tm:

# Installation

Navigate to where you'd like to install this, then do the following:

```
git clone https://github.com/BlueHephaestus/TombRaider
cd TombRaider
sudo bash build_deps.sh
```

This *should* simply install all the necessary apt and pip-python packages needed to run this out of the box. Please let me know or open a pull request if it's not!

# Command-Line Args

You can readily customise how you'd like to run TombRaider on your drive, using the following arguments:



# Walkthrough / How it Works

This tool would not exist without the already amazing tools out there, such as safecopy, testdisk, and more, many of which form the core parts of what this automates, tying many of them together. The full list of tools and resources can be found at the bottom of the page, so we will not go into each of them here.

This section covers each of the individual steps that Tomb Raider goes through in processing a device. Each will have a paragraph on what the step is, and then one on how we automate it.

## 1. Imaging

Imaging is going from a physical, messy, prone-to-error real device and putting it into a file so that it's virtual and easier / safer / more reliable to work with. This is what the `dd` command does often, for example. It reads raw data from whatever input you specify, and puts that in the output, as the same raw data. With disk imaging, this is converting from the block device plugged in, into a "image" file. This is the first step in data recovery, as it ensures we can continue regardless of what happens to the disk we're working with.

TR first uses safecopy - a more effective alternative to `ddrescue` (in my opinion) that gets more data than a raw `dd` read would, since it makes use of low level optimizations to get every little bit it can. We run through all 3 intensive stages of imaging to get as much as possible from possible bad areas. Do NOT unplug your device or anything while this is happening, it could create more issues and will immediately interrupt the imaging process.

## 2. Filesystem Recovery

This is where we attempt to recover the filesystem of the device, which contains all the filenames and locations and other metadata of data on the hard drive. This is often the part that's damaged when a hard drive just stops booting, in my experience, since if a part of it (since it's also on the disk) gets damaged, then it can't load any filesystem and thus can't boot. This is much like you have a library of books - your data, and a library catalog of those books - your filesystem. If the filesystem is lost, we can still get the books - since we already imaged the hard drive and got the entire library

