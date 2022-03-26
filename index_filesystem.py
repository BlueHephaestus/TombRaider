"""
index_filesystem.py

NOTE: This script is meant to be run AFTER condense_filesystem, to be run on the condensed filesystem,
    and use condensed filenames and format them without any problems or bugs arising.
    IF YOU ARE USING IT OUTSIDE THIS CONTEXT, USE AT YOUR OWN RISK.

Given a condensed filesystem folder containing sanitized filenames,
    produce a <foldername>.index file in the directory this script is run containing lines of the format:

    <foldername>/<filename>, <md5 hash of file contents>

For example, with the folder "testdisk/", this would produce testdisk.index, containing:
    testdisk/var|run|file1.txt, 912ec803b2ce49e4a541068d495ab570
    testdisk/usr|share|bin|script, 277f255555a1e4ff124bdacc528b815d
    testdisk/note.jpg, 01b08bb5485ac730df19af55ba4bb01c
    testdisk/file1, 912ec803b2ce49e4a541068d495ab570

The motivation for this is to be able to very quickly check if any two files' contents are equal or not equal,
    regardless of filenames. In this above example, for instance, we can see that var|run|file1.txt and file1 are
    actually the same file, just in a different location with a different filename. The filesystem can then be
    trimmed down in this manner, or other operations can be more efficiently done.

This script does not modify any files in the given directory, in any way. It will only read through them, and create
    an index file in the directory this script is run.
"""
import sys, os
import hashlib
from tqdm import tqdm
from filesystem_utils import *

def md5(fpath):
    # Quickly get md5 hash for file contents of fname
    hash_md5 = hashlib.md5()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def index(root):
    # Given a root folder, iterate through all filepaths to create
    # an index file as documented above.

    # Filename of index file is <filesystem folder>.index
    if root[-1] == "/": root = root[:-1]
    index_fname = os.path.basename(root) + ".index"
    with open(index_fname, "w") as index_f:
        for fpath in tqdm(fpaths(root)):
            # Get root-relative filename and digest of file contents
            fname = root + "/" + localize(fpath, root)
            digest = md5(fpath)
            index_f.write(f"{fname}, {digest}\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 index_filesystem.py filesystem/")

    root = sys.argv[1]
    index(root)
