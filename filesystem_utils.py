"""
filesystem_utils.py

Various multi-use utilities and tools for helping work with and manipulate files and filesystems.
"""

import os
import re
from tqdm import tqdm

def fpaths(dir):
    # Return a list of all filepaths in directory - not a generator.
    l = []
    for root,_,files in os.walk(dir):
        for f in files:
            l.append(os.path.join(root,f))
    return l

def localize(fpath, root, tombroot=False):
    # Given we are operating inside of the root filepath, return the localised version of fpath.
    # e.g. fpath=/usr/share/bin/script, root = /usr/share/bin/ -> return ./script
    # Has checks to make sure it doesn't leave extra slashes.
    # Will additionally remove testdisk and photorec if checking the tombroot (full root of operations)
    if tombroot:
        if "tomb/photorec" in fpath:
            fpath = re.sub('photorec\/photorec\.\d+\/', '', fpath, count=1)

        elif "tomb/testdisk" in fpath:
            fpath = re.sub('testdisk\/', '', fpath, count=1)


    # If root with trailing slash is in fpath, use that so we don't make a double slash
    if root[-1] != "/" and root+"/" in fpath:
        root += "/"

    # If root without trailing slash is in there, but root with trailing slash isn't,
    # remove the slash so we correctly remove root from the filepath str.
    elif root[-1] == "/" and root[:-1] in fpath:
        root = root[:-1]

    # Args are properly sanitized, we good to go.
    return fpath.replace(root, "")

def write_index(index, index_fname):
    # Write updated index to disk at index_fname.
    # NOTE: Uses index format of digest: fname, and writes to format "fname, digest".
    # We don't use a read-index because of how often the method of reading is modified per-file.
    with open(index_fname, "w") as f:
        for digest,fname in tqdm(index.items()):
            f.write(f"{fname}, {digest}\n")