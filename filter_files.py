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

def (index_fname, known_md5s_fname):
    # Given a directory index, check each entry in the index
    # against the digests in a file of known md5 digests, and for all matches,
    # remove the file from both our index and the directory.

    # Create known digests lookup table
    known = set({})
    with open(known_md5s_fname, "r") as f:
        for line in tqdm(f.readlines()):
            digest = line.strip()
            known.add(digest)

    index = {}
    with open(index_fname, "r") as f:
        for line in tqdm(f.readlines()):
            fname,digest = line.strip().split(", ")

            # If digest is known, remove
            if digest in known:
                os.remove(fname)

            # Otherwise load into the updated index
            else:
                index[digest] = fname

    # Write the updated index back to disk, we've already removed all duplicate files.
    write_index(index, index_fname)
    import magic
    import sys
    import mimetypes

    # print(magic.coerce_filename("/home/media/blue/001-SA-N-87/recup_dir.1/report.xml"))
    # print(magic.from_file(sys.argv[1],mime=True))
    # keep_going could be useful for later stuff, examining other possible matches
    # extension also useful but might do the same thing? going to keep both enabled when I use it just to be as comprehensive as possible.
    # uncompress also useful for examining inside of files - it even has support for lz4 and rar, possibly even more obscure ones. impressive.
    # For now going to stick with just trying to decompress everything then running this again however, since I don't have much gain to be had from
    # looking inside but not decompressing the file to a new directory.
    # now to get a extension from the output of this
    f = magic.Magic(keep_going=False, uncompress=False, extension=False)
    print(f.from_file(sys.argv[1]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 remove_known_files.py filesystem.index known.md5s")

    index = sys.argv[1]
    known_md5s_fname = sys.argv[2]
    remove_known_files(index, known_md5s_fname)
