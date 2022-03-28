"""
filter_files.py

Given a directory example/ and index example.index,
    this script will attempt to determine the filetype of every file in the directory and index using both
    existing extension and filedata, then sort the resulting filetype into subdirectories for each class.

If it obtains files which do not fit into the given classes or otherwise cause mismatches for the classification
    mechanism, they will be sorted into their own special files.

IMPORTANT NOTE ON FILTERING OUT:

If this script also obtains a blacklist file (a third argument), it will delete (filter out)
    all files with extensions OR classes matching those found in the blacklist file.
"""
import os,sys
from filesystem_utils import *
from tqdm import tqdm
from filter_utils import *


def filter_files(root, index_fname, blacklist_fname=None):
    # Given a directory, index, and optionally a blacklist,
    # Attempt to determine filetype and then sort the files by filetype, optionally filtering them out
    # by the blacklisted extensions/filetypes if a blacklist is provided.

    # Get files from index and ignore digests
    files = []
    with open(index_fname, "r") as f:
        for line in tqdm(f.readlines()):
            fname = line.strip().split(", ")[0]
            files.append(fname)

    # Get blacklist if there is one (will be empty if not)
    blacklist =set({})
    if blacklist_fname != None:
        with open(blacklist_fname, "r") as f:
           for line in f.readlines():
                entry = line.strip()
                blacklist.add(entry)

    """
    NOTE ON BLACKLIST: WE DO NOT REMOVE ANYTHING UNTIL WE HAVE DETERMINED THE FILETYPE, as determining the filetype 
        may determine that the extension of the file is different from the contents, and subsequently should not 
        be deleted but instead categorized as a mismatch or other anomaly class. For example, notes.h may
        look like a header file, but if we determine that it's actually an image, we'd instead put it in 
        the mismatches/ filetype folder. 
    So, we will not be using the blacklist until the very end of each per-file processing.
    
    DETERMINING FILETYPE
    
    We have two methods for determining filetype, which are then used for the resulting class the file will
        be associated to. 
        
    We first get a filetype classification from the extension:
        1. If there is no extension, the ext_class is UNKNOWN
        2. If the extension is in our supported mappings (extension -> filetype), the ext_class is that filetype
        3. If the extension is not in those mappings, the ext_class is UNSUPPORTED
        
    Then we get a filetype classification from the file data. We obtain info on the file data using pymagic,
        a python hook into the libmagic.c C library. We determine it from the pymagic output as follows:
        1. If the info is "data", then the data_class is UNKNOWN
        2. If the info is matched by our mappings / filter rules, the info_class is that filetype
        3. If the info is not matched by any of our rules, the info_class is UNSUPPORTED.
        
    We then use the ext_class and data_class to choose the final location of the file.
    """
    for fname in files:
        # Determine Ext class
        ext_class = filetype_from_ext(fname)

        # Determine Info class
        info_class = filetype_from_info(fname)

        # We now have ext class and info class.





    # Write the updated index back to disk, we've already removed all duplicate files.
    write_index(index, index_fname)

    # print(magic.coerce_filename("/home/media/blue/001-SA-N-87/recup_dir.1/report.xml"))
    # print(magic.from_file(sys.argv[1],mime=True))
    print(f.from_file(sys.argv[1]))


if __name__ == "__main__":
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print("Usage: python3 remove_known_files.py filesystem/ filesystem.index [blacklist_file]")

    root = sys.argv[1]
    index = sys.argv[2]
    if len(sys.argv) == 4:
        blacklist = sys.argv[3]
        filter_files(root, index, blacklist=blacklist)
    else:
        filter_files(root, index)
