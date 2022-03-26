"""
condense_filesystem.py

NOTE: Run with care. This will very likely modify ALL files inside the provided root folder.

Given a filesystem root folder, with any amount of subdirectories, at any level of nesting, with
    any number of files in any or all subdirectories, with any filenames for those files (including
    duplicate filenames or files with invalid characters)

THIS SCRIPT WILL
    1. Rename all files to contain their filepath
    2. Sanitize all resulting filenames and enforce a limited character set.
        Replacements (quotes only used for explanation):
            "-" becomes "_"
            " " becomes "_"
            "/" becomes "|"
            All remaining characters not a-z, A-Z, 0-9, _, or |  becomes "?"
    3. Move all now-sanitized files to the root folder, renaming by appending numbers if there are conflicts
        (This will remove them from their original location)
    4. Remove all leftover directories inside of root folder
    5. Exit.

This has the effect of condensing an entire filesystem into one folder, with tons of files in it, but with the
    entire structure of the original filesystem preserved, and filenames sanitized to avoid issues.

Examples:
    disk/
        assets/
            a weird name.css
            !!!#*)
            a
            b.txt
        img/
            jpg/
                2022/
                    cat.jpg
                    smug anime-face_35
                2021/
                    ---.jpg
                    ___.jpg
                    -_-.jpg
        asdf.txt
        asdf2.txt
        as-df.txt

    Becomes:
    disk/
        assets|a_weird_name.css
        assets|??????
        assets|a
        assets|b.txt
        img|jpg|2022|cat.jpg
        img|jpg|2022|smug_anime_face_35
        img|jpg|2021|___.jpg
        img|jpg|2021|___1.jpg
        img|jpg|2021|___11.jpg
        asdf.txt
        asdf2.txt
        as_df.txt

GUARANTEES:
    This script will NOT modify the root folder's name, and will NOT change anything outside of the root folder.
    No files are EVER deleted, overwritten, edited, or created
    All directories ARE deleted
    No file contents are ever modified in any way.
    FILE NAMES AND LOCATIONS ARE THE ONLY THING THIS SCRIPT MODIFIES.

Use at your own risk.

FINAL WARNING

USE THIS UNDER THE ASSUMPTION THAT IT WILL MODIFY FILE NAME AND/OR LOCATION OF ALL FILES IN THE DIRECTORY.
"""
import sys
import os
import re
import shutil
from tqdm import tqdm


def fpaths(dir):
    # Return a list of all filepaths in directory - not a generator, since we will be modifying the filenames.
    l = []
    for root,_,files in os.walk(dir):
        for f in files:
            l.append(os.path.join(root,f))
    return l

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
    os.replace(src, dst)
    return dst

def sanitize(fpath):
    # Given a filepath with any possible characters, sanitize and return the sanitized filepath.
    # Any possible characters does include unicode (hence regex for simple replaces)
    fpath = re.sub(r'[-\s]', '_', fpath, flags=re.UNICODE)
    fpath = re.sub(r'/', '|', fpath, flags=re.UNICODE)
    fpath = re.sub(r'[^a-zA-Z0-9._|]', '?', fpath, flags=re.UNICODE)
    return fpath

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

def condense(root):
    # Given a root folder, iterate through all folders and files to rename
    # and move the files as documented above.
    for fpath in tqdm(fpaths(root)):
        safemv(fpath, root + "/" + sanitize(localize(fpath, root)))

    # Remove any remaining directories if they are empty (we double check)
    for dir in os.listdir(root):
        dir = root + "/" + dir
        if os.path.isdir(dir) and len(fpaths(dir)) == 0:
            shutil.rmtree(dir)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 condense_filesystem.py filesystem/")

    root = sys.argv[1]
    condense(root)



















