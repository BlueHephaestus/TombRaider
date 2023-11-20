# Description

Automated Imaging, Undeletion, Recovery, Indexing, Organizing, Some Forensics, and Crypto Salvaging for any storage device Linux can recognize.

Given any hard drive, Tomb Raider will do everything in its power to recover as much data as possible on the drive, and do so entirely automatically. It was designed because I started wanting to do data recovery on any trashed hard drive I could find, and found myself repeating the same steps over and over for them, or skipping steps because I didn't want to spend the time constantly coming back to it and having to do yet another tedious step for one hard drive after another. I was finding hard drives faster than I could image them, and found myself spending all day doing this and obsessing over it - which wasn't nearly as fun as exploring them and seeing what cool stuff was on them.

And so, TombRaider came to be - a bot to automatically raid these "tombs" - old hard drives or new ones I'd find in various places or that friends would donate to me.

# Installation

Navigate to where you'd like to install this, then do the following:

```
git clone https://github.com/BlueHephaestus/TombRaider
cd TombRaider
sudo bash build_deps.sh
```

This *should* simply install all the necessary apt and pip-python packages needed to run this out of the box. Please let me know or open a pull request if it's not!

# Usage

After installation, simply call the script on the block device matching your disk - viewable with the `lsblk` command. /dev/sda, or /dev/md1 are examples.

This is only supported on Linux at the moment, since all the tools are readily available on Linux as well as interfacing directly with storage devices. Plus i'm lazy and Linux rulez.

Unfortunately requires sudo for full disk access. 

```
sudo bash tomb_raider.sh /dev/sdX
```

Aaaaand that's it! It may have higher or lesser requirements for host storage, and it may take hours or days depending on your resources and the specs / size of the storage device you're working with - the specifics of which will be covered in the Walkthrough section - but it's designed so you can just Plug and Play :tm:


### Command-Line Arguments

You can readily customise how you'd like to run TombRaider on your drive and which steps of the process you'd like to execute, using the following command-line arguments:

- `-d` or `--output-dir`
  - **Description**: Sets the output directory where the program should save its results.
  - **Usage**: `-d PATH` or `--output-dir PATH`
  
- `-nf` or `--no-image-file`
  - **Description**: Deletes the image file after the program has run, typically used to save disk space.
  - **Usage**: `-nf` or `--no-image-file`

- `-ns` or `--no-safecopy`
  - **Description**: Skips the safecopy process. It is assumed that a suitable image is available in place of the safecopy one.
  - **Usage**: `-ns` or `--no-safecopy`

- `-nt` or `--no-testdisk`
  - **Description**: Skips running testdisk.
  - **Usage**: `-nt` or `--no-testdisk`

- `-np` or `--no-photorec`
  - **Description**: Skips running photorec.
  - **Usage**: `-np` or `--no-photorec`

- `-nr` or `--no-raid`
  - **Description**: Skips the raiding process.
  - **Usage**: `-nr` or `--no-raid`

- `-nc` or `--no-crypto`
  - **Description**: Skips any process related to crypto salvaging.
  - **Usage**: `-nc` or `--no-crypto`

- `-na` or `--no-archive`
  - **Description**: Skips archiving or compressing processes.
  - **Usage**: `-na` or `--no-archive`

### Example Usages:
```
sudo bash tomb_raider.sh /dev/sda -d /home/user/raid -nf
```
- This will run TombRaider on /dev/sda, outputting to /home/user/raid, and will delete the image file after it's done.

```
sudo bash tomb_raider.sh disk.img -ns
```
 - This will run TombRaider on disk.img, skipping the safecopy process since an image file already exists.
```angular2html
sudo bash tomb_raider.sh /dev/sda -ns -nt
```
 - This will run TombRaider on /dev/sda, skipping the safecopy and photorec processes, useful if interrupted.

# Quick Overview of Features

For a given block device, disk image, or connected storage device, Tomb Raider will, in order, do the following:
1. **Imaging** - Utilises `safecopy` with multiple passes to image the device to an image file. Future ops all take place on the image.
2. **Filesystem Recovery** - Searches through partitions on the image, using `testdisk` to attempt to recover the filesystem, to preserve filesystem data, filenames, directories, etc. if possible.
3. **File Recovery** - Uses `photorec` to search the raw disk data, and recover any files that can be recovered, regardless of filesystem or partition table. These are usually named by their location on the physical disk, and may overlap with the files from testdisk.
4. **Raiding** - the meat of the program, navigates through the recovered files from both testdisk and photorec, and attempts to organise them into a more coherent and navigable format. 
   1. Files are MD5-hashed, then checked against a database of known files to minimize the amount of system files in the output.
   2. Hashes are checked against already-raided files to avoid duplicates. 
   3. System attempts to identify type of file based on file contents and file metadata. 
   4. Files are stored in a coherent directory structure based on type. 
   5. Files are stored in a `filesystem.index` file as they are found, to allow for easy searching and navigation of the output.
5. **Crypto Salvaging** - For those who are dumpster diving, or checking old hard drives for bitcoin. Searches for any mention of cryptocurrency, crypto-mining programs, and wallet files or wallet keys. Any matches found will be output to the terminal, and expect a lot of false positives if enabling this option. Checks keys last, so any keys with matching balances will be prominent in the output.
6. **Archiving** - Once all the files have been recovered and the tomb filesystem is created, it is archived into a `tomb.tar.lz4` file via archiving into a tarball, then compressing with lz4. 
   1. lz4 is used because it is a block-compression method and will not take as long to compress as gzip or bzip2, and is still a very efficient compression method. For filesystems of the size that Tomb Raider is designed to handle, gzip was found to hang for days and often never complete, while lz4 took minutes or hours.



# Walkthrough / How it Works

The following video gives a full walkthrough of how this tool works, however we will break down the steps here as well.
### BSides Las Vegas 2022 Presentation
https://www.youtube.com/watch?v=je-97WMp8KA&pp=ygUaYnNpZGVzIGx2IDIwMjIgdG9tYiByYWlkZXI%3D
<iframe width="1280" height="720" src="https://www.youtube.com/embed/je-97WMp8KA" title="GF - Tomb Raider - Automating Data Recovery and Digital Forensics" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

This tool would not exist without the already amazing tools out there, such as safecopy, testdisk, and more, many of which form the core parts of what this automates, tying many of them together. The full list of tools and resources can be found at the bottom of the page, so we will not go into each of them here.

This section covers each of the individual steps that Tomb Raider goes through in processing a device. Each will have a paragraph on what the step is, and then one on how we automate it.

## 1. Imaging

Imaging is going from a physical, messy, prone-to-error real device and putting it into a file so that it's virtual and easier / safer / more reliable to work with. This is what the `dd` command does often, for example. It reads raw data from whatever input you specify, and puts that in the output, as the same raw data. With disk imaging, this is converting from the block device plugged in, into a "image" file. This is the first step in data recovery, as it ensures we can continue regardless of what happens to the disk we're working with.

TR first uses safecopy - a more effective alternative to `ddrescue` (in my opinion) that gets more data than a raw `dd` read would, since it makes use of low level optimizations to get every little bit it can. We run through all 3 intensive stages of imaging to get as much as possible from possible bad areas. Do NOT unplug your device or anything while this is happening, it could create more issues and will immediately interrupt the imaging process.

## 2. Filesystem Recovery

This is where we attempt to recover the filesystem of the device, which contains all the filenames and locations and other metadata of data on the hard drive. This is often the part that's damaged when a hard drive just stops booting, in my experience, since if a part of it (since it's also on the disk) gets damaged, then it can't load any filesystem and thus can't boot. This is much like you have a library of books - your data, and a library catalog of those books - your filesystem. If the filesystem is lost, we can still get the books - since we already imaged the hard drive and got the entire library - however this step tries to recover the filesystem so we can have the names and proper organization of all of the data. Partitions are obtained using the `mmls` tool from The Sleuth Kit and then partitions are searched with `testdisk` to attempt to recover the filesystem.

## 3. File Recovery

Here we attempt to recover the files themselves, regardless of filesystem. This is like if you had a library of books, but the catalog was lost, so you had no idea what books you had, but you still had the books. This is where we use `photorec` to search through the raw data of the disk, and attempt to recover any files that can be recovered, regardless of filesystem or partition table. These are usually named by their location on the physical disk, and may overlap with the files from testdisk. This is the most intensive part of the process, and can take a very long time depending on the size of the disk and the amount of data on it. This is also the part that will recover the most data, since it's not limited by filesystem or partition table, and will recover any data it can find. 

Files may be false positives however, and may be corrupted or otherwise unusable. This is why we have the next step, which is the meat of the program.

## 4. Raiding

This is the meat of the program, where we take the recovered files from both testdisk and photorec, and attempt to organise them into a more coherent and navigable format as well as condense the results considerably. It does this by doing the following:
 - Files are MD5-hashed, then checked against a database of known files to minimize the amount of system files in the output. These files are obtained from NIST's NSRL database, which is a database of known files and their hashes. This is used to filter out system files, since we don't want to recover those, and they're often the most common files on a system which take up space in our resulting output.
 - Hashes are checked against already-raided files to avoid duplicates. This is done by storing the hashes of all files that have already been raided in an index file called `filesystem.index`, and then checking the hashes of the files we're currently raiding against that index. If the hash is already in the file, then we know we've already raided that file, and we can skip it. This is to avoid duplicates, and to save time and space in the output. 
 - System attempts to identify type of file based on file contents and file metadata. This is done by using the `file` command / `libmagic`, which attempts to identify the type of file based on the contents of the file, as well as manual lookup of the file extension in categorical tables. This, along with the index, is used to organize the files into folders based on type, so that we can easily navigate the output and find what we're looking for.
 - As files are stored, their filenames are sanitized to remove any characters that may cause issues with the filesystem, such as `~` or `*`. This is done by replacing any of these characters with a `?` instead, so that the filename is still readable, but will not cause issues with the filesystem. Additionally, files maintain their original location on the drive (if known from testdisk recovery) in the filename, so that we can still see where they were on the drive, with the directories separated by `|`. 
 - Future versions will attempt to recreate the original filesystem organization using this notation.

## 5. Crypto Salvaging

This is the next-to-final step, which makes use of multiple tags and search criteria (several of which have been obtained from `Autopsy`, a data forensic tool) to do several passes through the filesystem, doing the following:
 - Check each filename
 - Check each file's contents (takes the longest)
 - Check any possible wallet keys against the blockchain to see if they're valid and have a balance.

As these are searched, any matches are output and highlighted in red to the terminal. Due to the large amount of tags, there are often false positives due to webpages or cache files having mention of bitcoin or other cryptocurrencies, so it's important to check each result to ensure it's valid. This is also why the output is highlighted in red, so that it's easy to see and identify.

This feature may be modified to be optional considering the highly verbose nature of its output.

# Tools Used

- Safecopy - https://safecopy.sourceforge.net/
- TestDisk - https://www.cgsecurity.org/wiki/TestDisk
- PhotoRec - https://www.cgsecurity.org/wiki/PhotoRec
- MMLS (The Sleuth Kit) - https://sleuthkit.org/
- NIST NSRL - https://www.nist.gov/itl/ssd/software-quality-group/national-software-reference-library-nsrl
- Autopsy - https://sleuthkit.org/

Thanks for reading! If you have any questions, feel free to reach out at bluehephaestus@gmail.com, and if you have any suggestions or contributions, feel free to make a pull request or open an issue!











