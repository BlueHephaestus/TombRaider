"""
merge_testdisk_photorec.py

Given condensed, indexed, and de-duplicated directories for testdisk and photorec,

    1. Find any pairs of files that have matching contents (using the indexes), and remove
    the photorec part of the pair, since the testdisk version will have greater than or equal to
    the amount of file metadata as the photorec version.

    2. Move all remaining (inherently unique) files to a new filesystem/ directory, and merge
    the contents of both indexes into a new filesystem.index file.

    3. Remove the original two directories and original two indexes.
"""
import os,sys
import shutil

from filesystem_utils import *
from tqdm import tqdm

def read_index(index_fname):
    # Assumes unique elements in the index (otherwise it will overwrite values), as in this file.
    index = {}
    with open(index_fname, "r") as f:
        for line in tqdm(f.readlines()):
            fname, digest = line.strip().split(", ")
            index[digest] = fname
    return index

def merge_testdisk_photorec(testdisk_root, testdisk_index_fname, photorec_root, photorec_index_fname, fs_root, fs_index_fname):
    # Given testdisk root + index, and photorec root + index, merge the two into a new
    # filesystem/ root with filesystem.index using the process documented above.

    # Result/Destination filesystem
    fs_index = {}

    # Load both indexes
    testdisk_index = read_index(testdisk_index_fname)
    photorec_index = read_index(photorec_index_fname)

    # Find any pairs, and handle all photorec files
    for digest,fname in tqdm(photorec_index.items()):
        if digest in testdisk_index:
            # Remove the photorec version, don't add it to result index (meaning it will be discarded at end)
            os.remove(fname)
        else:
            # Keep the photorec version since it's unique - move it to result filesystem and result index
            fs_fname = fs_root + os.path.basename(fname)
            os.replace(fname, fs_fname)
            fs_index[digest] = fs_fname

    # Handle / Move all testdisk files
    for digest,fname in tqdm(testdisk_index.items()):
        fs_fname = fs_root + os.path.basename(fname)
        os.replace(fname, fs_fname)
        fs_index[digest] = fs_fname

    # Write updated index (before deleting anything)
    write_index(fs_index, fs_index_fname)

    # Testdisk and PhotoRec filesystems have now been merged into the Result / Destination Filesystem
    # Remove original testdisk and photorec filesystems and indexes
    shutil.rmtree(testdisk_root)
    shutil.rmtree(photorec_root)
    os.remove(testdisk_index_fname)
    os.remove(photorec_index_fname)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 merge_testdisk_photorec.py testdisk/ testdisk.index photorec/ photorec.index filesystem/ filesystem.index")

    testdisk_root = sys.argv[1]
    testdisk_index = sys.argv[2]
    photorec_root = sys.argv[3]
    photorec_index = sys.argv[4]
    fs_root = sys.argv[5]
    fs_index = sys.argv[6]
    merge_testdisk_photorec(testdisk_root, testdisk_index, photorec_root, photorec_index, fs_root, fs_index)
