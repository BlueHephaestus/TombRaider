from bit import Key
from bit.format import bytes_to_wif
import re
import sys
import os
import tqdm
import mmap
from tqdm import tqdm
from filesystem_utils import sanitize

# Format is ["Label", True/False (if regex), "Rule"]
# NOTE: ALMOST ALL OF THESE ARE FROM AUTOPSY

# Many of the patterns are duplicated with variations to increase match possibilities with our sanitization
# We remove the things that force beginning and end of string matches for example
ruleset = [
["Atomic Wallet", False, "atomic wallet.exe"],
["Bitcoin Armory", False, "armoryqt.exe"],
["Bitcoin Wallet", False, "bitcoin-qt.exe"],
["Bitcoin Anything", False, "bitcoin"],
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


def salvage(priv):
	# Given private key string candidate, mutate it and try different permutations to try and obtain a possible original key.
	# priv: near-64 character string. (62, 63, or 64)
	#
	# Private key size can be either 32 or 31 bytes, end result. This means 62,63,or 64 characters in total - 3 possibilities
	# each time they can also be either in wif compressed, wif uncompressed, or hex format, so that's 3 more possibilities.
	# 
	# So for a given key we will make 9 api calls, and each takes at most .2seconds, meaning that you can expect a runtime of 1.8s/key.
	
	# Start with cuts, pad it with zeros to give len 64 if needed
	assert len(priv) in [62,63,64]
	d = 64-len(priv)
	priv += "0"*d

	# more general but not needed and it's harder to read
	#cuts = [priv[:64-i] for i in range(3):]

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
		#tqdm.write(f"Key: {priv} Address: {key_compressed.address} Balance: {key_compressed_bal}")
		#tqdm.write(f"Key: {priv} Address: {key_uncompressed.address} Balance: {key_uncompressed_bal}")
		if key_compressed_bal != 0.0 or key_uncompressed_bal != 0.0:
			print("#"*100)
			print(f"Key: {priv} Address: {key_compressed.address} Balance: {key_compressed_bal}")
			print(f"Key: {priv} Address: {key_uncompressed.address} Balance: {key_uncompressed_bal}")
			print("#"*100)
			# I know it's bad practice but this never happens anyways
			sys.exit("JACKPOT! VALID PRIVATE KEY WITH BALANCE FOUND! EXITING EARLY...")
		

def fpaths(directory):
	# Not a generator so tqdm likes it
	l = []
	for root,subdirs,files in os.walk(directory):
		for f in files:
			l.append(os.path.join(root,f))

	return l

def key_hex_candidates(fpath):
	candidates = []
	try:
		with open(fpath, "rb") as f:
			candidates= re.findall(b'\x01\x01\x04\x20(.{32})', f.read())
	except MemoryError:
		print(f"Encountered Very Large File {fpath} ({round(os.path.getsize(fpath)/1000000000, 2)} GB)\n \
			  Attempting a Memory Mapping to read through it, this may take a moment.")
		try:
			with open(fpath, 'r+') as f:
				data = mmap.mmap(f.fileno(), 0)
				candidates = re.findall(b'\x01\x01\x04\x20(.{32})', data)
			print("Successfully Read File, Continuing")
		except:
			print("Memory Map Read failed, skipping")


	return candidates


if __name__ == "__main__":
	# Given any directory, scour it for any trace of cryptocurrency usage and any private keys.
	# Will check all files for any private key contents, and check all filenames for anything matching our rulesets.
	data = sys.argv[1]

	keys = set({})

	print("Iterating through directory to check filenames against rulesets and obtain candidate private keys...")
	for fpath in tqdm(fpaths(data)):

		# Check filepath against our rules
		apply_ruleset(fpath)

		# Get candidates
		candidates = key_hex_candidates(fpath)
		for priv in candidates:
			keys.add(priv.hex())

	print(f"Preprocessing complete, {len(keys)} Candidates Obtained. Testing...")
	pbar = tqdm(keys)
	for key in pbar:
		pbar.set_description("Candidate: " + key)
		salvage(key)








