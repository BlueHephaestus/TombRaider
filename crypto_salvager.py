import re
import sys
from tqdm import tqdm

import filesystem_utils
from filesystem_utils import sanitize

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
["Dash Electrum Wallet", True, "electrum-dash(.*).exe"],
["Dash Electrum Wallet", True, "electrum_dash(.*).exe"],

["Dogecoin", False, "dogecoin-qt.exe"],
["Eidoo Wallet", False, "eidoo.exe"],
["Electron Cash", False, "electron-cash.exe"],

#og with slight mods (already lowercase)
["Electron Cash Portable", True, "electron-cash(.*)portable.exe"],
["Electron Cash Standalone", True, "electron-cash(.*).exe"],
["Electrum", True, "electrum(.*).exe"],
["Electrum Portable", True, "electrum(.*)portable.exe"],

# sanitized
["Electron Cash Portable", True, "electron_cash(.*)portable.exe"],
["Electron Cash Standalone", True, "electron_cash(.*).exe"],
["Electrum", True, "electrum(.*).exe"],
["Electrum Portable", True, "electrum(.*)portable.exe"],

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
["Qtum Electrum", True, "Qtum-electrum-win-(.*).exe"],
["Qtum Electrum", True, "qtum-electrum-win-(.*).exe"],
["Qtum Electrum", True, "qtum_electrum_win_(.*).exe"],

["Stargazer Wallet", False, "stargazer.exe"],
["Toast Wallet", False, "toastwallet.exe"],
["Trezor Bridge", False, "trezord.exe"],
["Verge Tor QT Wallet", False, "verge-qt.exe"],
["Zecwallet", False, "Zecwallet Fullnode.exe"],
["Zecwallet Lite", False, "Zecwallet Lite.exe"],
["Zel Core", False, "zelcore.exe"],
["Zel Core Portable", False, "zelcore-portable.exe"],

# our own customs
["Bitcoin Anything", False, "bitcoin"],
["Dogecoin Anything", False, "dogecoin"],
["Ethereum Anything", False, "ethereum"],
["CryptoCurrency Anything", False, "cryptocurrency"],

]
# Compile any regexes before using
for i,rule in enumerate(ruleset):
    if rule[1]:
        ruleset[i][2] = re.compile(rule[2])

def apply_ruleset(fpath):
    # Given a fpath, check it against all of our rules, and print any matches.
    matches = []
    for rule in ruleset:
        label,is_regex,pattern = rule
        if is_regex:
            # Rule is Regex, apply and check
            # No need to modify pattern since we already did that in the ruleset, plus if we did then we'd have
            # to recompile. This just runs variants on the fpath instead. This will run all combinations as a result.
            if bool(re.search(pattern, fpath)) or bool(re.search(pattern, fpath.lower())) or bool(re.search(pattern, sanitize(fpath))):
                # pattern match, save this
                matches.append((label, pattern))


        else:
            # Rule is simple substring check, check lowercase and sanitized versions as well
            if pattern in fpath or pattern.lower() in fpath or sanitize(pattern) in fpath:
                matches.append((label, pattern))

    # Print any matches
    for label, pattern in matches:
        print(f"MATCH FOUND: '{label}' with pattern '{pattern}' matched for filepath '{fpath}'")

def apply_ruleset_in_file(fpath):
    matches = []
    with open(fpath,'rb') as f:
        for i,line in enumerate(f):
            line = line.decode("ascii", "ignore")
            for rule in ruleset:
                label,is_regex,pattern = rule
                if is_regex:
                    if bool(re.search(pattern, line)):
                        matches.append((label, pattern, i))
                else:
                    if pattern in line or pattern.lower() in line or sanitize(pattern) in line:
                        matches.append((label, pattern, i))

    # Print any matches
    for label, pattern, line_i in matches:
            print(f"MATCH FOUND: '{label}' with pattern '{pattern}' matched for filepath '{fpath}' on line {i}")


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









