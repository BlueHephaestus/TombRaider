"""
Tool to go through tombs and print out per-subdirectory and per-extension data,
    specifically the filecounts and average filesizes.

Will output these to a filesystem.stats file and
"""
import sys
import os
import re
import shutil
import hashlib
from filesystem_utils import *
from tqdm import tqdm
import traceback
from filter_utils import *
from collections import defaultdict

# All possible subdirectories from tomb raider results.
# Only counts if it's tomb/{subdir}
TOMB_SUBDIRS = set([
    "Encrypted",
    "Archives",
    "Videos",
    "Audio",
    "Images",
    "Programs",
    "Documents",
    "Irrelevant",
    "Misc",
    "Mismatches",
    "Unsupported_Filedata",
    "Unknown_Filedata",
    "Unsupported_Extension",
    "Unknown",
    "Unsupported_Text",
    "Small_Images",
    ])

nformat = lambda n: f'{n:,}'.rjust(10)
sformat = lambda s: (f'{round(s / 1000000000., 2):.2f}' + ' GB').rjust(10)
pformat = lambda p: (f'{round(p*100, 2):.2f}' + " %").rjust(10)


def rowprint(f, key, n, s, total_n, total_s, header=False):
    # if header don't compute percentages just print
    if header:
        s = f"{key.ljust(21)} | {n.rjust(10)} | {s.rjust(10)} | {total_n.rjust(10)} | {total_s.rjust(10)}"
    else:
        s = f"{key.ljust(21)} | {nformat(n)} | {sformat(s)} | {pformat(n / total_n)} | {pformat(s / total_s)}"
    print(s)
    f.write(s + "\n")


def analyse(tombs_root):
    """
    Given a bunch of tombs, will get total # of files (nums) and total filesize (sizes) of all of them.
    Then for every tomb subdirectory (in all tombs), will get the total # of files in each, and total size of each,
        over all tombs.
    Will do the same for extensions.

    Will output all sizes in GB, and will further compute % of totals and output separately.

    Will print this and also write it to a file.

    :param tombs_root: Directory containing arbitrary number of subdirectories with "tomb/" directories.
    """

    # Dicts to keep track of everything, no nested values. e.g. sizes["txt"] = 430 (for 430 cumulative bytes of txt)
    nums = defaultdict(lambda:0) # num of files, default to 0
    sizes = defaultdict(lambda:0) # total size of files, default to 0

    for fpath in tqdm(fpaths(tombs_root)):
        # Only check if it's in a tomb
        if "/tomb/" not in fpath:
            continue

        # We can further extend this to only check if it's in a tomb's subdirectory, since otherwise it wasn't
        # put there by TR.
        subdirs = fpath.split("/")
        i = subdirs.index("tomb")+1
        if i > len(subdirs)-1 or subdirs[i] not in TOMB_SUBDIRS:
            # not in a subdir or not in one of ours, skip
            continue

        # Else we have tomb subdir
        subdir = subdirs[i]

        # Get ext and size of file
        ext = os.path.splitext(fpath)[-1].lower()
        try:
            size = os.path.getsize(fpath)
        except OSError:
            continue

        # Increment stats counters for both subdir and extension
        if len(ext) == 0:
            ext = "NO_EXT"
        nums[ext] += 1
        sizes[ext] += size
        nums[subdir] += 1
        sizes[subdir] += size

    # Write and Print Stats
    total_n = sum([v for k,v in nums.items() if k in TOMB_SUBDIRS])
    total_s = sum([v for k,v in sizes.items() if k in TOMB_SUBDIRS])

    with open("filesystem.stats", "w") as f:
        rowprint(f,"CLASSIFICATION", "TOTAL #", "TOTAL SIZE", "% OF #", "% OF SIZE", header=True)
        for subdir in sorted(TOMB_SUBDIRS):
            n,s = nums[subdir], sizes[subdir]
            rowprint(f,subdir,n,s,total_n,total_s)
        for key in sorted(list(nums.keys())):
            if key not in TOMB_SUBDIRS and len(key) < 7:
                # ext = key
                n,s = nums[key], sizes[key]
                rowprint(f,key,n,s,total_n,total_s)
        rowprint(f,"TOTAL", total_n, total_s, total_n, total_s)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 analyse_tombs.py tombs_root/")

    tombs_root = sys.argv[1]
    analyse(tombs_root)



















