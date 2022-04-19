import sys
import os
import re
from filesystem_utils import *
from tqdm import tqdm
from filter_utils import *
from hash_utils import *
import numpy as np
from collections import defaultdict


def get_filetype_subdir(fname):
    # Determine it's type, so we can know if its in blacklist and should be deleted.
    # Determine Ext class
    ext_class = filetype_from_ext(fname)

    # Determine Info class
    info_class = filetype_from_info(fname)

    # We now have ext class and info class.
    # We now sort them - if the classes agree, they go in that class. If they don't, then we have a lot
    # of possible conditions for which we handle for how they get sorted, detailed in the below conditionals.
    if ext_class == info_class:
        # Easy case, put it in the class
        subdir = ext_class

    elif known(ext_class) and known(info_class) and ext_class != info_class:
        # Both known, but mismatch
        subdir = "Mismatches"

    elif known(ext_class) and unsupported(info_class):
        # We know the ext but data is something else
        if plaintext(fname):
            # Some type of text file, trust the extension in this case
            subdir = ext_class
        else:
            # If it's not plaintext then we put it here.
            subdir = "Unsupported_Filedata"

    elif known(ext_class) and unknown(info_class):
        # We know the ext but not the data
        subdir = "Unknown_Filedata"

    elif unsupported(ext_class) and known(info_class):
        # We know the data but ext is something else
        subdir = "Unsupported_Extension"

    elif unsupported(ext_class) and unknown(info_class):
        # Has some extension but no info obtained, unknown data
        subdir = "Unknown"

    elif unknown(ext_class) and known(info_class):
        # We trust data when we are lacking an extension
        subdir = info_class

    elif unknown(ext_class) and unsupported(info_class):
        # No extension, filedata is something unsupported
        if plaintext(fname):
            # Some type of text file, store in special directory
            subdir = "Unsupported_Text"
        else:
            # If it's not plaintext then we put it here.
            subdir = "Unsupported_Filedata"

    # There are no other combinations - trust me, I spent hours writing out the cases.

    # Sort images roughly so we can filter out a lot of icons
    if subdir == "Images":
        if small_image(fname):
            subdir = "Small_Images"

    return subdir


def process(testdisk_root, photorec_root, filesystem_root, known_md5s_fname, blacklist_fname=None):

    # Get optimal hashing buffer size to maximize speed for it
    get_optimal_md5_buffer_size()

    # Counts of what files we find
    subdir_counts = defaultdict(lambda:1) # Default values to 1

    # Get blacklist if there is one (will be empty if not)
    blacklist = set({})
    if blacklist_fname != None:
        print(f"Loading blacklist file {blacklist_fname}")
        with open(blacklist_fname, "r") as f:
            for line in f.readlines():
                entry = line.strip()
                blacklist.add(entry)

    # Load all hashes
    # We tried many tests to find the fastest way to load this data (since it was taking max. two minutes originally)
    # We tried chunking the file and parallelizing the operations, as well as making each parallel process create
    # a subset that got added together into the final set - this got it down to one minute max.
    # However, we found that using .npy files from numpy was the most feasible and also fastest method, giving us
    # around 20 seconds for the loads, even with an 'object' class object. If numpy supported uint128 objects like
    # the md5 hashes are in, this could be saved as a numpy binary file, however they don't support that datatype
    # yet and I didn't bother to get into the math of converting them into numbers and back again.
    # POSSIBLE UPGRADE: Could use some hash that gets it as 64 bits, to convert it to uint64, or could just
    # split the 128 hash into two uint64s and keep them in pairs. For now though this gets around the annoying limit
    # I was encountering on loading these 4gb files.
    # Also it requires we use a nparray to store them and then use it's `searchsorted` function on it, which is about
    # 4x slower than set contains, however they're both so damn fast that on 600,000 lookups searchsorted took a TOTAL
    # of 2 seconds compared to set.contains .5 seconds. So we good to go.
    print(f"Loading known hashes file {known_md5s_fname}. This may take a moment...")
    known_md5s = np.load(known_md5s_fname, allow_pickle=True)
    n = len(known_md5s)
    def isknown(digest):
        # Wish they could just have a contains method but oh heckin well
        i = np.searchsorted(known_md5s, digest)
        return i != 0 and i != n and known_md5s[i] == digest

    # Since inserting into a numpy array would copy the array and is therefore way too costly,
    # we have a separate set for any new digests we find to compare for duplicates.
    found_md5s = set({})
    def isfound(digest):
        return digest in found_md5s

    # Do one pass, eliminating as many files as possible if we don't need them as we go.
    # This, I've found, is the best way to maximize speed and minimize disk space used.
    index = {}

    # Iterate through testdisk first, since we only keep a photorec file if it's got new content
    # because testdisk will have the file metadata such as location and name.
    print(f"Raiding Testdisk and Photorec Recovered Filesystems and Creating Tomb Filesystem")
    for fpath in tqdm(fpaths(testdisk_root) + fpaths(photorec_root)):
        # HASH CHECKS
        # First check if we can delete it
        # This will check both our list of knowns, and the one we've accumulated since the program started
        digest = md5(fpath)
        if isknown(digest) or isfound(digest):
            os.remove(fpath)
            continue
        # Else add to our list of founds.
        found_md5s.add(digest)

        # Get filetype
        subdir = get_filetype_subdir(fpath)
        subdir_counts[subdir] += 1

        if subdir in blacklist:
            os.remove(fpath)
            continue

        # Finally we know it's a keeper, so we condense it's filename and add it to the index.
        subdir = filesystem_root + "/" + subdir
        if not os.path.isdir(subdir):
            os.mkdir(subdir)

        # # Store in index
        condensed_fpath= subdir + "/" + sanitize(localize(fpath, filesystem_root, tombroot=True))
        safemv(fpath, condensed_fpath)
        index[digest] = condensed_fpath

    # Write Index
    write_index(index, filesystem_root + "/" + "filesystem.index")
    # Remove any remaining directories if they are empty
    print("Removing Leftover Testdisk and PhotoRec files")
    remove_leftover_dirs(testdisk_root)
    remove_leftover_dirs(photorec_root)


if __name__ == "__main__":
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        print("Usage: python3 raid_filesystem.py testdisk_root/ photorec_root/ filesystem_root/ sorted_known.md5s [blacklist]")

    testdisk_root = sys.argv[1]
    photorec_root = sys.argv[2]
    filesystem_root = sys.argv[3]
    known_md5s_fname = sys.argv[4]
    testdisk_root = addslash(testdisk_root)
    photorec_root = addslash(photorec_root)
    filesystem_root = addslash(filesystem_root)
    if len(sys.argv) == 6:
        blacklist = sys.argv[5]
        process(testdisk_root, photorec_root, filesystem_root, known_md5s_fname, blacklist_fname=blacklist)
    else:
        process(testdisk_root, photorec_root, filesystem_root, known_md5s_fname)



















