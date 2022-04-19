"""
Tool to go through all tombs and print stats on storage space saved by creating hashsets across all tombs.
    Does this to maximize speed since it otherwise takes forever, and uses only filesize to check files for equality
"""
from filesystem_utils import *
from hash_utils import *
from reprint import output

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


def rowstr(key, n, s, total_n, total_s, header=False):
    # if header don't compute percentages just print
    if header:
        s = f"{key.ljust(21)} | {n.rjust(10)} | {s.rjust(10)} | {total_n.rjust(10)} | {total_s.rjust(10)}"
    else:
        s = f"{key.ljust(21)} | {nformat(n)} | {sformat(s)} | {pformat(n / total_n)} | {pformat(s / total_s)}"
    return s

def safesize(fpath):
    try:
        return os.path.getsize(fpath)
    except OSError:
        return 0

def hash(tombs_root):
    """
    Given a bunch of tombs, will hash every file, building a hash set from all of them.
        Will also keep track of the size of each file as we go, so that at the end we can print
        total size of all files checked
        total size of files hashsed
        total size of files that would be deleted
        possible resulting size after deleting duplicate files

    :param tombs_root: Directory containing arbitrary number of subdirectories with "tomb/" directories.
    """

    total_n = 0
    total_size = 0
    hash_n = 0
    hash_size = 0
    dupe_n = 0
    dupe_size = 0
    found_md5s = set({})
    with output(initial_len=4, interval=10) as out:
        for fpath in fpaths(tombs_root):
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

            # Get hash and size of file
            #digest = md5(fpath)
            #digest = fasthash(fpath)
            #digest = md5(fpath)
            size = safesize(fpath)
            #digest = fasthash(fpath, size)
            digest = size

            total_n += 1
            total_size += size
            if digest in found_md5s:
                dupe_n += 1
                dupe_size += size
            else:
                hash_n += 1
                hash_size += size
                found_md5s.add(digest)

            # Write and Print Stats
            out[0] = rowstr("CLASSIFICATION", "TOTAL #", "TOTAL SIZE", "% OF #", "% OF SIZE", header=True)
            out[1] = rowstr("HASHES",hash_n, hash_size, total_n, total_size)
            out[2] = rowstr("DUPES",dupe_n,dupe_size,total_n,total_size)
            out[3] = rowstr("TOTAL", total_n, total_size, total_n, total_size)








if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 hash_tombs.py tombs_root/")

    tombs_root = sys.argv[1]
    hash(tombs_root)



















