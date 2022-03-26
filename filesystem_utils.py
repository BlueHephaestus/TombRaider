"""
filesystem_utils.py

Various multi-use utilities and tools for helping work with and manipulate files and filesystems.
"""

import os

def fpaths(dir):
    # Return a list of all filepaths in directory - not a generator.
    l = []
    for root,_,files in os.walk(dir):
        for f in files:
            l.append(os.path.join(root,f))
    return l

def localize(fpath, root):
    # Given we are operating inside of the root filepath, return the localised version of fpath.
    # e.g. fpath=/usr/share/bin/script, root = /usr/share/bin/ -> return ./script
    # Has checks to make sure it doesn't leave extra slashes.

    # If root with trailing slash is in fpath, use that so we don't make a double slash
    if root[-1] != "/" and root+"/" in fpath:
        root += "/"

    # If root without trailing slash is in there, but root with trailing slash isn't,
    # remove the slash so we correctly remove root from the filepath str.
    elif root[-1] == "/" and root[:-1] in fpath:
        root = root[:-1]

    # Args are properly sanitized, we good to go.
    return fpath.replace(root, "")
