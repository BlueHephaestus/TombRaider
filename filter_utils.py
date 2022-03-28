"""
filter_utils.py

Provides Utils for using the tags and extension constants configured in filters.py to obtain filetypes
    from tags and extensions, as well as other useful tools for filtering and filetype classifying files.

Important Note: NO EXTS ARE SHARED BETWEEN GROUPS, NO TAGS ARE SHARED BETWEEN GROUPS. ALL ARE UNIQUE.
"""
import os
from filters import *
import magic

# Extension checks ordered in rough estimate of complexity (or perhaps average entropy) of filetype
exts = [ENCRYPTION_EXTS, ARCHIVE_EXTS, VIDEO_EXTS, AUDIO_EXTS, IMAGE_EXTS, PROGRAM_EXTS, DOCUMENT_EXTS, IRRELEVANT_EXTS, MISC_EXTS]
tags = [ENCRYPTION_TAGS, ARCHIVE_TAGS, VIDEO_TAGS, AUDIO_TAGS, IMAGE_TAGS, PROGRAM_TAGS, DOCUMENT_TAGS, IRRELEVANT_TAGS, MISC_TAGS]
labels = ["Encrypted",   "Archive",    "Video",    "Audio",    "Image",    "Program",    "Document",    "Irrelevant",    "Misc"]

# get extension, check if extension in groupings

# primary tags are the extension name - if one of the tags is an extension, then that takes precedence over other tags.
# secondary tags are the given tags
# see if extension in filedata string - this is just our way of checking each grouping against the filedata string
# its our extra tags - every ext in a group is a tag for that group

# get filedata string, check each tag in string against filetype tags

# Pymagic to determine info from file contents (and magic numbers hence the name)
get_info = magic.Magic(keep_going=False, uncompress=False, extension=False)

def filetype_from_ext(fname):
    # Determine which grouping the ext belongs to (can only belong to one)
    ext = os.path.splitext(fname)[-1]
    if len(ext) <= 1:
        # No extension, or just a dot, unknown
        return "Unknown"

    ext = ext[1:] # remove the dot
    for i, grp in enumerate(exts):
        if ext in grp:
            return labels[i]

    # Has an extension but it's not in any of our lists, unsupported
    return "Unsupported"


def filetype_from_info(fname):
    """
    Determine which grouping the info str belongs to by checking each word in the str against tags and extensions.
    We break the infostr into "tags", the words that make it up split by spaces.

    Then we first check if any of the tags are valid extensions in any groupings - if they are, we return that as
        the grouping for this info string.

    Otherwise we check each tab grouping for if any of the tags in those groupings match up to tags in our string.
    We do the loops in this order so that we are only checking one group at a time, since we have the groups ordered
        in an order to suit this method - so that in the case of multiple matching tags, we will be more likely
        to get the one that indicates the highest complexity.

    For example, if an info string was "Temporary Encrypted File". Temporary is in Irrelevant, so if we checked
        by tags first rather than groups first, we would immediately classify as Irrelevant. But if we first iterate
        through groups and check which are in our string, we would first encounter Encrypted tags and identify
        that this was an encrypted file, which we care much more about.

    Other Examples:
        "Audio / Video File" -> Should be video, not audio.
        "Subtitle Audio Track" -> Should be audio, not irrelevant.
        "Compressed Heavy Documentation" -> Should be archive, not document.
        "Encrypted Archive" -> Should be encrypted, not archive.
    """
    info = get_info.from_file(fname)
    info = info.lower()
    infotags = set(info.split(" "))

    # Check if we have the ["data"] case, where we couldn't get any info from the file, which is unknown.
    if info == "data":
        return "Unknown"

    # First check if any tags match extensions
    for i,grp in enumerate(exts):
        for ext in grp:
            if ext in infotags:
                return labels[i]

    # Then check if any tags match our tags
    for i,grp in enumerate(tags): #Iterate through groups first
        for tag in grp:
            if tag in infotags:
                # Found matching tag
                return labels[i]

    # Has info but it's not in any of our lists, unsupported
    return "Unsupported"

