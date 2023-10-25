import re
import sys
import os
from tqdm import tqdm

import filesystem_utils
from filesystem_utils import sanitize

from bit import Key
from bit.format import bytes_to_wif
import mmap
import traceback
from termcolor import colored

# Format is ["Label", True/False (if regex), "Rule"]
# NOTE: ALMOST ALL OF THESE ARE FROM AUTOPSY

# Many of the patterns are duplicated with variations to increase match possibilities with our sanitization
# We remove the things that force beginning and end of string matches for example
ruleset = [
["Atomic Wallet", False, "atomic wallet.exe"],
["Bitcoin Armory", False, "armoryqt.exe"],
["Bitcoin Wallet", False, "bitcoin-qt.exe"],
["Wallet Data File", False, "wallet.dat"], # mine
["Bither", False, "BitherWinLauncher.exe"],
["BitPay", False, "bitpay.exe"],
["Canoe", False, "canoe.exe"],
["Coinomi Wallet", False, "coinomi.exe"],
["Copay", False, "copay.exe"],
["Dash Core Wallet", False, "dash-qt.exe"],

# Og and sanitized
["Dash Electrum Wallet", True, "electrum-dash(.{0,80}).exe"],
["Dash Electrum Wallet", True, "electrum_dash(.{0,80}).exe"],

["Dogecoin", False, "dogecoin-qt.exe"],
["Eidoo Wallet", False, "eidoo.exe"],
["Electron Cash", False, "electron-cash.exe"],

#og with slight mods (already lowercase)
["Electron Cash Portable", True, "electron-cash(.{0,80})portable.exe"],
["Electron Cash Standalone", True, "electron-cash(.{0,80}).exe"],
["Electrum", True, "electrum(.{0,80}).exe"],
["Electrum Portable", True, "electrum(.{0,80})portable.exe"],

# sanitized
["Electron Cash Portable", True, "electron_cash(.{0,80})portable.exe"],
["Electron Cash Standalone", True, "electron_cash(.{0,80}).exe"],
["Electrum", True, "electrum(.{0,80}).exe"],
["Electrum Portable", True, "electrum(.{0,80})portable.exe"],

["Exodus", False, "exodus.exe"],
["GreenAddress Wallet", False, "GreenAddress Wallet.exe"],
["Guarda Wallet", False, "guarda.exe"],
["Jaxx", False, "jaxx liberty.exe"],
["Ledger", False, "Ledger Live.exe"],
["Lisk Wallet", False, "lisk.exe"],
["Litecoin", False, "litecoin-qt.exe"],
["Monero GUI Wallet", False, "monero-wallet-gui.exe"],
["MultiBit", False, "multibit-hd.exe"],
["Multidoge Wallet", False, "multidoge.exe"],
["NanoVault", False, "NanoVault.exe"],
["Neon Wallet", False, "neon.exe"],
["Qtum Core", False, "qtum-qt.exe"],

# og, lower, and sanitized
["Qtum Electrum", True, "Qtum-electrum-win-(.{0,80}).exe"],
["Qtum Electrum", True, "qtum-electrum-win-(.{0,80}).exe"],
["Qtum Electrum", True, "qtum_electrum_win_(.{0,80}).exe"],

["Stargazer Wallet", False, "stargazer.exe"],
["Toast Wallet", False, "toastwallet.exe"],
["Trezor Bridge", False, "trezord.exe"],
["Verge Tor QT Wallet", False, "verge-qt.exe"],
["Zecwallet", False, "Zecwallet Fullnode.exe"],
["Zecwallet Lite", False, "Zecwallet Lite.exe"],
["Zel Core", False, "zelcore.exe"],
["Zel Core Portable", False, "zelcore-portable.exe"],

# our own customs
["Bitcoin Anything", False, "Bitcoin"],
["Dogecoin Anything", False, "Dogecoin"],
["Ethereum Anything", False, "Ethereum"],
["CryptoCurrency Anything", False, "Cryptocurrency"],

]
# Compile any regexes before using
for i,rule in enumerate(ruleset):
    if rule[1]:
        # add context regex in case this matches and we want to see where
        ruleset[i].append(re.compile('.{0,80}' + rule[2] + '.{0,80}'))

        ruleset[i][2] = re.compile(rule[2])
    else:
        ruleset[i].append("ew no")

# Preprocess these string ops so we don't repeat them a million times
for i,rule in enumerate(ruleset):
    label, is_regex, pattern, context_pattern = rule
    if not is_regex:
        pattern_lower = pattern.lower()
        pattern_sanitize = sanitize(pattern)
        ruleset[i][2] = [pattern, pattern_lower, pattern_sanitize]

def apply_ruleset(fpath):
    # Given a fpath, check it against all of our rules, and print any matches.
    matches = []
    for rule in ruleset:
        label,is_regex,pattern,_ = rule
        if is_regex:
            # Rule is Regex, apply and check
            # No need to modify pattern since we already did that in the ruleset, plus if we did then we'd have
            # to recompile. This just runs variants on the fpath instead. This will run all combinations as a result.
            if bool(re.search(pattern, fpath)) or bool(re.search(pattern, fpath.lower())) or bool(re.search(pattern, sanitize(fpath))):
                # pattern match, save this
                matches.append((label, pattern))


        else:
            # Rule is simple substring check, check lowercase and sanitized versions as well
            pattern, pattern_lower, pattern_sanitize = pattern
            if pattern in fpath or pattern_lower in fpath or pattern_sanitize in fpath:
                matches.append((label, pattern))

    # Print any matches
    for label, pattern in matches:
        print(f"MATCH FOUND: '{label}' with pattern '{pattern}' matched for filepath '{fpath}'")

GB = 1024*1024*1024
MB = 1024*1024
KB = 1024
def file_chunked_lines(fpath, large_file_size=GB, chunk_size=MB):
    """
    Given a file, read the file in chunks, and yield the lines separated by \n in each chunk,
        so that we are iterating over lines in the file, but not loading the whole file into memory,
        instead reading it in chunks of size chunk_size, then separating it into lines,
        and keeping the last line of each chunk so that we do not miss any matches that may be split across chunks.

    :param fpath: The file to read
    :param large_file_size: If the file is larger than this, we will use a progress bar (Bytes)
    :param chunk_size: The size of each chunk to read  (Bytes)
    :return: Yields lines from the file
    """
    if not os.path.isfile(fpath): return # handles named pipes and fake files

    # Check if file is large
    file_size = os.path.getsize(fpath)
    large_file = file_size > large_file_size

    # If not large, skip all this and read it all into memory
    # if not large_file:
    #     with open(fpath, 'rb') as f:
    #         for line in f:
    #             yield line
    #     return
    #
    # If large, read in chunks with progress bar

    # If large, use a progress bar
    if large_file:
        pbar = tqdm(total=file_size/MB, unit="MB")

    with open(fpath, 'rb') as f:
        overlap = b""
        while True:
            chunk = f.read(chunk_size)
            if large_file:
                pbar.update(chunk_size/MB)
            if not chunk and not overlap:
                break
            chunk = overlap + chunk
            lines = chunk.split(b'\n')

            # If there's more data, keep the last line as overlap into next chunk
            if len(lines) > 1:
                overlap = lines.pop()
            else:
                overlap = b""

            for line in lines:
                yield line
    if large_file:
        pbar.close()
    return

def apply_ruleset_in_file(fpath):
    matches = []
    #candidates = re.findall(b'\x01\x01\x04\x20(.{32})', f.read())
    for line_i, line in enumerate(file_chunked_lines(fpath)):
        line = line.decode("ascii", "ignore")
        for rule in ruleset:
            label, is_regex, pattern, context_pattern = rule
            #if not is_regex:
            #line = line.decode("ascii", "ignore")

            if is_regex:
                if pattern.search(line):
                    matches.append((line_i, line, rule))

            else:
                pattern, pattern_lower, pattern_sanitize = pattern
                if pattern in line or pattern_lower in line or pattern_sanitize in line:
                    matches.append((line_i, line, rule))
        line_i+=1


    # Alternate method, line based approach
    # with open(fpath,'rb') as f:
    #     #lines = f.read()#.decode("ascii","ignore"
    #     #try:
    #     #lines = f.read().decode("ascii","ignore")
    #     #except MemoryError:
    #     #print("Encountered Memory Error on decode, skipping...")
    #     #return
    #     # TODO change back to full read if not large file???
    #     if large_file: mb_read = 0
    #
    #     pbar = tqdm(total=mb_file_size, disable=not large_file, unit="MB")
    #     line_i = 0
    #     for line in f:
    #         line = line.decode("ascii","ignore")
    #         if len(line) > 10000:print(len(line))
    #         if large_file:
    #             #mb_read += len(line) / 10e6
    #             pbar.update(len(line)/1e6)
    #
    #         for rule in ruleset:
    #             label, is_regex, pattern, context_pattern = rule
    #             if is_regex:
    #                 if pattern.search(line):
    #                     matches.append((line_i, line, rule))
    #             else:
    #                 pattern, pattern_lower, pattern_sanitize = pattern
    #                 if pattern in line or pattern_lower in line or pattern_sanitize in line:
    #                     matches.append((line_i, line, rule))
    #
    #             #
    #             # if is_regex:
    #             #     if bool(re.search(pattern, line)):
    #             #         matches.append((line_i, line, rule))
    #             # else:
    #             #     pattern, pattern_lower, pattern_sanitize = pattern
    #             #     if pattern in line or pattern_lower in line or pattern_sanitize in line:
    #             #         matches.append((line_i, line, rule))
    #         line_i += 1
    #     pbar.close()

    # Print any matches with context, if there are any.
    if len(matches) > 0:
        print()
        print(f"MATCHES FOUND FOR FILEPATH {colored(fpath,'green')}:")
    for line_i, line, (label, is_regex, pattern,context_pattern) in matches:
        if is_regex:
            print(f"\t{pattern} match:{colored(re.findall(pattern, line), 'red')}")
        else:
            pattern, pattern_lower, pattern_sanitize = pattern
            s = ""
            if pattern in line:
                p = pattern
            elif pattern_lower in line:
                p = pattern_lower
            elif pattern_sanitize in line:
                p = pattern_sanitize
            idx = line.index(p)
            #s = f"\t{p} match:" + lines[idx - 80:idx] + colored(lines[idx:idx + len(p)], 'red') + lines[idx + len(p):idx + 80 + len(p)]
            s = f"\t{p} match:" + line[max(idx - 80,0):idx] + colored(line[idx:(idx + len(p))], 'red') + line[(idx + len(p)):idx + 80 + len(p)]
            s = s.replace('\r', ' ').replace('\n', ' ')
            print(s)
        #print(f"MATCH FOUND: '{label}' with pattern '{pattern}' matched for filepath '{fpath}' on line {i}")



candidate_pattern = re.compile(b'\x01\x01\x04\x20(.{32})')
def key_hex_candidates(fpath):
    candidates = []
    for line_i, line in enumerate(file_chunked_lines(fpath)):
        candidates.extend(re.findall(candidate_pattern, line))
    return candidates


def salvage(priv):
    # Given private key string candidate, mutate it and try different permutations to try and obtain a possible original key.
    # priv: near-64 character string. (62, 63, or 64)
    #
    # Private key size can be either 32 or 31 bytes, end result. This means 62,63,or 64 characters in total - 3 possibilities
    # each time they can also be either in wif compressed, wif uncompressed, or hex format, so that's 3 more possibilities.
    #
    # So for a given key we will make 9 api calls, and each takes at most .2seconds, meaning that you can expect a runtime of 1.8s/key.

    # Start with cuts, pad it with zeros to give len 64 if needed
    assert len(priv) in [62, 63, 64]
    d = 64 - len(priv)
    priv += "0" * d

    # more general but not needed and it's harder to read
    # cuts = [priv[:64-i] for i in range(3):]

    # 3 possible cutoffs.
    cuts = [priv[:62], priv[:63], priv[:64]]

    # Try each one on all parse methods
    for priv in cuts:
        try:
            key = Key.from_hex(priv).to_bytes()
        except ValueError:
            # Invalid Key, skip.
            continue
        key_compressed = Key(bytes_to_wif(key, compressed=True))
        key_uncompressed = Key(bytes_to_wif(key, compressed=False))

        key_compressed_bal = float(key_compressed.get_balance('btc'))
        key_uncompressed_bal = float(key_uncompressed.get_balance('btc'))
        # tqdm.write(f"Key: {priv} Address: {key_compressed.address} Balance: {key_compressed_bal}")
        # tqdm.write(f"Key: {priv} Address: {key_uncompressed.address} Balance: {key_uncompressed_bal}")
        if key_compressed_bal != 0.0 or key_uncompressed_bal != 0.0:
            print("#" * 100)
            print(f"Key: {priv} Address: {key_compressed.address} Balance: {key_compressed_bal}")
            print(f"Key: {priv} Address: {key_uncompressed.address} Balance: {key_uncompressed_bal}")
            print("#" * 100)
            print("JACKPOT! VALID PRIVATE KEY WITH BALANCE FOUND!")


if __name__ == "__main__":
    # Given any directory, scour it for any trace of cryptocurrency usage and / or crypto programs / keyfiles
    # Optimized for speed and giving reliable indicators if there is something worth investigating on a given drive.
    # Used to iterate through all files manually, and also check the contents of them for any possible private keys,
    # then manually try those against the bitcoin API. This was very costly and didn't produce any results,
    # so we're going with the much faster, flag-if-anything-comes-up (since this is rare) approach.

    output_dir = sys.argv[1]
    index_fpath = output_dir + "/" + "filesystem.index"
    keys = set({})

    print("Checking Index Filepaths against Rulesets...")

    try:
        with open(index_fpath, "r") as f:
            # Iterate directly through it and check filenames line by line.
            fpaths = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print("No index found, creating one...")
        fpaths = filesystem_utils.fpaths(output_dir)

    for line in tqdm(fpaths):
        fpath = line.split(", ")[0]

        # Check filepath against our rules
        apply_ruleset(fpath)

    print("Checking Index Filepath Contents against Rulesets...")
    with tqdm(bar_format='{desc}', position=0) as desc_pbar:
        for line in tqdm(fpaths):
            fpath = line.split(", ")[0]
            desc_pbar.set_description(fpath[-100:])

            # Check file contents against our rules
            #print(fpath)
            apply_ruleset_in_file(fpath)

    keys = set({})
    # Do manual wallet key checking
    print("Checking for any wallet files / keys...")
    for line in tqdm(fpaths):
        fpath = line.split(", ")[0]
        # Get candidates
        candidates = key_hex_candidates(fpath)
        for priv in candidates:
            keys.add(priv.hex())

    print(f"{len(keys)} Candidates Obtained. Testing...")
    pbar = tqdm(keys)
    for key in pbar:
        pbar.set_description("Candidate: " + key)
        salvage(key)








