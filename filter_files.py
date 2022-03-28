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

    subdir_counts = {}

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
    
    We also have some special cases for plaintext files, because EVERYTHING IS PLAINTEXT AAAAAA
    """
    # Helper lambdas
    known = lambda c: c != "Unknown" and c != "Unsupported"
    unknown = lambda c: c == "Unknown"
    unsupported = lambda c: c == "Unsupported"
    index = {}
    with open(index_fname, "r") as f:
        for line in tqdm(f.readlines()):
            fname, digest = line.strip().split(", ")

            # Determine Ext class
            ext_class = filetype_from_ext(fname)

            # Determine Info class
            info_class = filetype_from_info(fname)

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
                if plaintext(fname):
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
                if plaintext(fname):
                    # Some type of text file, store in special directory
                    subdir = "Unsupported_Text"
                else:
                    # If it's not plaintext then we put it here.
                    subdir = "Unsupported_Filedata"

            # There are no other combinations - trust me, I spent hours writing out the cases.

            # Sort images roughly so we can filter out a lot of icons
            if subdir == "Images":
                if small_image(fname):
                    subdir = "Small_Images"


            if subdir not in subdir_counts:
                subdir_counts[subdir] = 1
            else:
                subdir_counts[subdir] += 1

            if subdir not in blacklist:
                # We now have subdirectory, move the file to that and make the directory if not made yet.
                # we don't create all the directories at first since it's very plausible that some won't be used
                subdir = root + "/" + subdir
                dst_fname = subdir + "/" + os.path.basename(fname)
                if not os.path.isdir(subdir):
                    os.mkdir(subdir)

                # Finally move the file
                os.replace(fname, dst_fname)

                # Store in index
                index[digest] = dst_fname

            else:
                # Blacklisted, remove it
                os.remove(fname)

    # Write the updated index back to disk, we've moved everything
    write_index(index, index_fname)

    # Print distribution of classes
    print("Found and sorted the following distribution of classes:")
    counts = list((subdir,count) for subdir,count in subdir_counts.items())
    sorted_counts = sorted(counts, key=lambda x:x[1])
    for subdir, count in sorted_counts:
        print(f"\t{subdir}: {count} Files")

if __name__ == "__main__":
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print("Usage: python3 remove_known_files.py filesystem/ filesystem.index [blacklist_file]")

    root = sys.argv[1]
    index = sys.argv[2]
    if root[-1] == "/": root = root[:-1]
    if len(sys.argv) == 4:
        blacklist = sys.argv[3]
        filter_files(root, index, blacklist_fname=blacklist)
    else:
        filter_files(root, index)
