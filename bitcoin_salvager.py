from bit import Key
from bit.format import bytes_to_wif
import re
import sys
import os
import tqdm
import mmap
from tqdm import tqdm

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
				#mo = re.search('error: (.*)', data)
				candidates = re.findall(b'\x01\x01\x04\x20(.{32})', data)
			print("Successfully Read File, Continuing")
		except:
			print("Memory Map Read failed, skipping")


	return candidates

# FROM ORIGINAL, FOR REFERENCE
# Uncomment for security, set the address and uncomment.
#address = "ADDRESS_TO_SEND_TO"
#print(float(key.get_balance('btc')))
#if (float(key.get_balance('btc')) > 0):
#tx = key.send([], leftover=address)
		

if __name__ == "__main__":
	# Given data, try to salvage a BTC private key from it.
	# may be raw hex key string of len 62,63,or 64, a file containing one, or a directory containing files possibly containing one.
	data = sys.argv[1]

	# DATA TYPE
	# Default
	dtype = "file"

	# has separator (directory)
	if os.sep in data:
		dtype = "dir"

	# has 62-64 characters (hex string)
	elif len(data) in [62,63,64]:
		dtype = "hex"

	indent = 0
	keys = set({})

	if dtype == "dir":
		print("Directory Detected. Obtaining candidate private keys...")
		for fpath in tqdm(fpaths(data)):
			candidates = key_hex_candidates(fpath)
			for priv in candidates:
				keys.add(priv.hex())


	elif dtype == "file":
		print("File Detected. Obtaining candidate private keys...")
		candidates = key_hex_candidates(data)
		for priv in candidates:
			keys.add(priv.hex())

	elif dtype == "hex":
		print("Hex String Detected. Obtaining candidate private keys...")
		keys.add(data)

	print(f"Preprocessing complete, {len(keys)} Candidates Obtained. Testing...")
	for key in tqdm(keys):
		tqdm.write(key)
		salvage(key)








