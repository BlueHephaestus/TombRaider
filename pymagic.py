import magic
import sys
import mimetypes

#print(magic.coerce_filename("/home/media/blue/001-SA-N-87/recup_dir.1/report.xml"))
#print(magic.from_file(sys.argv[1],mime=True))
#keep_going could be useful for later stuff, examining other possible matches
#extension also useful but might do the same thing? going to keep both enabled when I use it just to be as comprehensive as possible.
# uncompress also useful for examining inside of files - it even has support for lz4 and rar, possibly even more obscure ones. impressive.
# For now going to stick with just trying to decompress everything then running this again however, since I don't have much gain to be had from
# looking inside but not decompressing the file to a new directory.
# now to get a extension from the output of this
f = magic.Magic(keep_going=False,uncompress=False,extension=False)
print(f.from_file(sys.argv[1]))

