"""
Go through a tomb raided using the old system and recreate the filesystem using the new system.
"""
import sys
import os
import re
from utils.filesystem_utils import *
#from tqdm import tqdm
from utils.filter_utils import *
from utils.hash_utils import *
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


def process(tomb_root):

    # Do one pass, eliminating as many files as possible if we don't need them as we go.
    # This, I've found, is the best way to maximize speed and minimize disk space used.
    index = {}

    print(f"Re-creating Updated Tomb Filesystem")


    filesystem_dir = "Filesystem/"
    recovered_dir = "Recovered_Files/"
    if not os.path.exists(filesystem_dir):
        os.makedirs(filesystem_dir)
    with open(os.path.join(tomb_root, "filesystem.index"), "r") as f:
        # Iterate directly through it and check filenames line by line.
        index = {}
        for line in f.readlines():
            # Get the filename and the hash
            fpath, digest = line.strip().split(", ")
            index[digest] = fpath

    for fpath in tqdm(fpaths(tomb_root)):

        # If file has | in it then it's a filepath, otherwise keep it in its subdirectory.
        if "|" in fpath:
            # Remove tomb/subdir from fpath via getting it to its basename
            new_fpath = os.path.basename(fpath)
            new_fpath = new_fpath.replace("|", "/")
            new_fpath = os.path.join(filesystem_dir, new_fpath)
            safemv(fpath, new_fpath)
        else:
            new_fpath = fpath.replace("tomb", "Recovered_Files")

        index[digest] = new_fpath
    # Move sorted subdirs (all non-Filesystem) into recovered files directory
    for subdir in os.listdir(tomb_root):
        if subdir != filesystem_dir:
            safemv(os.path.join(tomb_root, subdir), os.path.join(recovered_dir, subdir))

    # Write Index
    write_index(index, "filesystem.index")
    remove_leftover_dirs(tomb_root)
    # Remove any remaining directories if they are empty
    # print("Removing Leftover Testdisk and PhotoRec files")
    # remove_leftover_dirs(testdisk_root)
    # remove_leftover_dirs(photorec_root)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 recreate_filesystem.py tomb/")

    tomb_root = sys.argv[1]
    process(tomb_root)



















