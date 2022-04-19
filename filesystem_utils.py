"""
filesystem_utils.py

Various multi-use utilities and tools for helping work with and manipulate files and filesystems.
"""

import os
import re
from tqdm import tqdm
import shutil
import traceback
import sys

# Number of characters to limit our filenames to. We keep it at 240 so we still have some room for renaming
# before reaching 255 characters, when we later sort into subdirectories.
FPATH_TRIM_LENGTH = 240

addslash = lambda root: root[:-1] if root[-1] == "/" else root

def fpaths(dir):
    # Return a list of all filepaths in directory - not a generator.
    l = []
    print("Getting list of all filepaths...")
    n = 0
    for root,_,files in os.walk(dir):
        for f in files:
            l.append(os.path.join(root,f))
            n += 1
            sys.stdout.write(f"\r{str(f'{n:,}').rjust(13)} files iterated")
    sys.stdout.flush()
    print()
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

def remove_leftover_dirs(root):
    for dir in os.listdir(root):
        dir = root + "/" + dir
        if os.path.isdir(dir) and len(fpaths(dir)) == 0:
            shutil.rmtree(dir)

def safemv(src, dst):
    # Move file at location src to location dst, renaming it if needed to avoid any destruction of data.
    if os.path.exists(dst) and src != dst:
        # If a copy exists, instead rename to filename.txt.1, filename.txt.2, filename.txt.3,
        # etc. until we have a unique filename
        dst_copy = dst + ".{}"
        i = 1
        while os.path.exists(dst_copy.format(i)):
            i += 1

        # Found a value not taken, format
        dst = dst_copy.format(i)

    # Move now that we have no replacement of data (despite the name) guaranteed
    # We return dst filename in case we want to use that later. And b/c it might be changed.
    try:
        os.replace(src, dst)
        return dst
    except OSError as e:
        if e.args[0] != 22:
            raise
        print(f"OS ERROR 22 ENCOUNTERED MOVING {src} TO {dst}. YOU ARE LIKELY EITHER OUT OF DISK SPACE OR USING"
              f"A NON-EXT4 FORMATTED FILESYSTEM, CAUSING AN ERROR DUE TO FILE NAMING.")
        print(traceback.format_exc())

def sanitize(fpath):
    # Given a filepath with any possible characters, sanitize and return the sanitized filepath.
    # Any possible characters does include unicode (hence regex for simple replaces)
    fpath = re.sub(r'[-\s]', '_', fpath, flags=re.UNICODE)
    fpath = re.sub(r'/', '|', fpath, flags=re.UNICODE)
    fpath = re.sub(r'[^a-zA-Z0-9._|]', '?', fpath, flags=re.UNICODE)
    fpath = fpath[:FPATH_TRIM_LENGTH]
    return fpath
