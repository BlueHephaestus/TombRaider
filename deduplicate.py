"""
To run only the portion of TombRaider that removes duplicates of files and known files.
Also makes an index of files.
run:
python3 deduplicate.py filesystem_root/ sorted_known.md5s
"""

import sys
import os
import re
from utils.filesystem_utils import *
#from tqdm import tqdm
from utils.hash_utils import *
import numpy as np
from collections import defaultdict
from bloom_filter2 import BloomFilter

"""
I have done. So many tests. To see what's fastest here.

For one, making this only work on duplicates and not on "known"s is way faster.
Also, not using a bloom filter is also about 3x as fast.
Also also, using a smaller more naive md5 hash of just the first CHUNK_SIZE and last CHUNK_SIZE bytes
    of the file (8kb in this case) is like 7x as fast as the alternative, 
    since it's O(k) where k is chunk size rather than O(n) where n is file size.
    
So now it runs in what used to take 2 hours in about 23 seconds on my test OS of ~742,000 files. 
So it's a little faster.
"""

def process(filesystem_root):

    # Get optimal hashing buffer size to maximize speed for it
    #get_optimal_md5_buffer_size()

    # Load bloom filter
    # bloom_filter = BloomFilter(max_elements=150_000_000, error_rate=0.001, filename=('known.bloom',-1), start_fresh=False) # 132 mil known hashes
    # fpath_iter = fpaths(filesystem_root)
    # bloom_filter = BloomFilter(max_elements=len(fpath_iter), error_rate=1e-5)

    # Load all hashes
    # print(f"Loading known hashes file {known_md5s_fname}. This may take a moment...")
    # known_md5s = np.load(known_md5s_fname, allow_pickle=True)

    # Populate Bloom Filter with knowns
    #print(f"Populating Bloom Filter...")
    # for digest in tqdm(known_md5s):
    #     bloom_filter.add(digest)
    # print(bloom_filter)
    # print(known_md5s[0] in bloom_filter)

    # print("Saving Bloom Filter...")
    # bloom_filter.save("bloom_filter.bf")

    # Definitive checks
    # n = len(known_md5s)
    # def isknown(digest):
    #     # Wish they could just have a contains method but oh heckin well
    #     i = np.searchsorted(known_md5s, digest)
    #     return i != 0 and i != n and known_md5s[i] == digest

    removed = 0
    removed_size = 0
    hits = 0
    index = {}
    def isfound(digest):
        return digest in index

    # Do one pass, eliminating as many files as possible if we don't need them as we go.
    # This, I've found, is the best way to maximize speed and minimize disk space used.
    print(f"Removing Duplicates and Known Files...")
    for fpath in tqdm(fpaths(filesystem_root)):
        # HASH CHECKS
        # First check if we can delete it based on the bloom filter
        # Most of the time we will not delete it since they're often not in the bloom filter
        if not os.path.isfile(fpath):continue
        #if os.path.getsize(fpath) > 1e8: continue
        digest = fast_lossy_md5(fpath)
        # digest = md5(fpath)
        # if digest in bloom_filter:
            # Might be in the bloom filter, so we have to check the definitive checks
            # this is costly part, try to make it as fast as possible
            # Fast certainty check first
            # have to do full md5 for the known ones
            # hits += 1
        if isfound(digest):
            #if isknown(digest) or isfound(digest):
            # If it's in there, delete it
            removed += 1
            removed_size += os.path.getsize(fpath)
            os.remove(fpath)
            continue
        # Otherwise it's not in the bloom filter, so we have to add it to the bloom filter and index
        # clever conditionals so that this will only happen if it's not in either
        # bloom_filter.add(digest)
        index[fpath] = digest

    print("Writing index to disk...")
    write_index(index, filesystem_root + "/" + "filesystem.index")
    print(f"Removed {removed} files totalling {removed_size/1e9}GB.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 deduplicate.py filesystem_root/")

    filesystem_root = sys.argv[1]
    # known_md5s_fname = sys.argv[2]
    filesystem_root = addslash(filesystem_root)
    process(filesystem_root)


