"""
remove_known_files.py

Given a directory index example.index, and a list of known md5 digests known.md5s,
    this script will remove all files inside the directory and index which have md5 digests found inside
    the list of known md5 digests. This list of known md5 digests represents file contents which are
    common and found in normal software, so we treat these as irrelevant and discard them.
"""
import os,sys
from filesystem_utils import *
from tqdm import tqdm

def remove_known_files(index_fname, known_md5s_fname):
    # Given a directory index, check each entry in the index
    # against the digests in a file of known md5 digests, and for all matches,
    # remove the file from both our index and the directory.

    # Create known digests lookup table
    known = set({})
    with open(known_md5s_fname, "r") as f:
        for line in tqdm(f.readlines()):
            digest = line.strip()
            known.add(digest)

    index = {}
    with open(index_fname, "r") as f:
        for line in tqdm(f.readlines()):
            fname,digest = line.strip().split(", ")

            # If digest is known, remove
            if digest in known:
                os.remove(fname)

            # Otherwise load into the updated index
            else:
                index[digest] = fname

    # Write the updated index back to disk, we've already removed all duplicate files.
    write_index(index, index_fname)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 remove_known_files.py filesystem.index known.md5s")

    index = sys.argv[1]
    known_md5s_fname = sys.argv[2]
    remove_known_files(index, known_md5s_fname)
