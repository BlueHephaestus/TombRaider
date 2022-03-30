import sys
import os
import re
import shutil
import hashlib
from filesystem_utils import *
from tqdm import tqdm
import traceback
from filter_utils import *

# Number of characters to limit our filenames to. We keep it at 240 so we still have some room for renaming
# before reaching 255 characters, when we later sort into subdirectories.
FPATH_TRIM_LENGTH = 240
known = lambda c: c != "Unknown" and c != "Unsupported"
unknown = lambda c: c == "Unknown"
unsupported = lambda c: c == "Unsupported"


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

def md5(fpath):
    # Quickly get md5 hash for file contents of fname
    hash_md5 = hashlib.md5()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process(src_root, dst_root, known_md5s_fname, blacklist_fname=None):
    subdir_counts = {}

    # Get blacklist if there is one (will be empty if not)
    blacklist =set({})
    if blacklist_fname != None:
        with open(blacklist_fname, "r") as f:
            for line in f.readlines():
                entry = line.strip()
                blacklist.add(entry)

    # Load all hashes
    known_md5s = set({})
    with open(known_md5s_fname, "r") as f:
        for line in tqdm(f.readlines()):
            digest = line.strip()
            known_md5s.add(digest)

    # Do one pass, eliminating as many files as possible if we don't need them.
    index = {}
    seen_digests = set({}) # since we may add some to the index but only after checking if blacklisted.
    for fpath in tqdm(fpaths(src_root)):
        # First check if we can delete it
        digest = md5(fpath)
        if digest in known_md5s or digest in seen_digests:
            os.remove(fpath)
            continue
        seen_digests.add(digest)

        # Determine it's type, so we can know if its in blacklist and should be deleted.
        # Determine Ext class
        ext_class = filetype_from_ext(fpath)

        # Determine Info class
        info_class = filetype_from_info(fpath)

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
            if plaintext(fpath):
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
            if plaintext(fpath):
                # Some type of text file, store in special directory
                subdir = "Unsupported_Text"
            else:
                # If it's not plaintext then we put it here.
                subdir = "Unsupported_Filedata"

        # There are no other combinations - trust me, I spent hours writing out the cases.

        # Sort images roughly so we can filter out a lot of icons
        if subdir == "Images":
            if small_image(fpath):
                subdir = "Small_Images"

        if subdir not in subdir_counts:
            subdir_counts[subdir] = 1
        else:
            subdir_counts[subdir] += 1

        if subdir in blacklist:
            os.remove(fpath)
            continue

        # Finally we know it's a keeper, so we condense it's filename and add it to the index.
        subdir = dst_root + "/" + subdir
        if not os.path.isdir(subdir):
            os.mkdir(subdir)

        # # Store in index
        condensed_fname= subdir + "/" + sanitize(localize(fpath, dst_root))
        safemv(fpath, condensed_fname)
        index[digest] = condensed_fname

    # Remove any remaining directories if they are empty (we double check)
    for dir in os.listdir(src_root):
        dir = src_root + "/" + dir
        if os.path.isdir(dir) and len(fpaths(dir)) == 0:
            shutil.rmtree(dir)


if __name__ == "__main__":
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        print("Usage: python3 process_filesystem.py src_filesystem/ dst_folder/ known.md5s [blacklist]")

    src_root = sys.argv[1]
    dst_root = sys.argv[2]
    known_md5s_fname = sys.argv[3]
    if src_root[-1] == "/": src_root = src_root[:-1]
    if dst_root[-1] == "/": dst_root = dst_root[:-1]
    if len(sys.argv) == 5:
        blacklist = sys.argv[4]
        process(src_root, dst_root, known_md5s_fname, blacklist_fname=blacklist)
    else:
        process(src_root, dst_root, known_md5s_fname)



















