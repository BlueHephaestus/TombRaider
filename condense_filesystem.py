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
from filesystem_utils import *
from tqdm import tqdm
import traceback

# Number of characters to limit our filenames to. We keep it at 240 so we still have some room for renaming
# before reaching 255 characters, when we later sort into subdirectories.
FPATH_TRIM_LENGTH = 240
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



















