"""
remove_indexed_duplicates.py

Given an already-indexed directory example/ and example.index, this script will
    remove all files inside the directory and index which have matching md5 digests,
    since we make the "hash assumption" that this means they are equivalent in their contents.
"""
import os,sys
from filesystem_utils import *
from tqdm import tqdm

def remove_indexed_duplicates(root, index_fname):
    # Given a root directory and index of that directory,
    # Use the index to quickly identify duplicate files in the directory,
    # and remove them from both the index and the directory.

    index = {}
    with open(index_fname, "r") as f:
        for line in tqdm(f.readlines()):
            fname,digest = line.strip().split(", ")

            # If file with these contents exists, remove this one
            if digest in index:
                os.remove(fname)

            # Otherwise add this to the index
            else:
                index[digest] = fname

    # Write the updated index back to disk, we've already removed all duplicate files.
    write_index(index, index_fname)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 remove_indexed_duplicates.py filesystem/ filesystem.index")

    root = sys.argv[1]
    index = sys.argv[2]
    remove_indexed_duplicates(root, index)
