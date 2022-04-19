import os
import time
from tqdm import tqdm
import numpy as np
import hashlib

MD5_BUFFER_SIZE = 2**17  # (~.12 million) default unless we run function to get the optimal value for this sytem

def get_optimal_md5_buffer_size():
    # Run md5 hash on an arbitrary 500MB file with different buffer sizes
    # to determine the fastest buffer size for this machine.

    print("Determining System-Wide Optimal MD5 Buffer Size")
    # 500mb random content file
    f = open("md5test","wb")
    f.write(os.urandom(500000000)) #500 million
    f.close()

    # Time to time from 1024 to 4,194,304
    sizes = [2**(i) for i in range(10, 22)]
    times = [0]*len(sizes)
    for i,size in enumerate(tqdm(sizes)):
        start = time.time()
        hash_md5 = hashlib.md5()
        with open("md5test", "rb") as f:
            for chunk in iter(lambda: f.read(size), b""):
                hash_md5.update(chunk)
        end = time.time()-start
        times[i] = end

    optimal_buffer_size = sizes[np.argmin(times)]
    global MD5_BUFFER_SIZE #Update global usevar
    MD5_BUFFER_SIZE = optimal_buffer_size
    print(f"Determined {optimal_buffer_size} as Optimal Buffer Size")
    os.remove("md5test")
    return optimal_buffer_size

def md5(fpath):
    # Quickly get md5 hash for file contents of fname
    hash_md5 = hashlib.md5()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(MD5_BUFFER_SIZE), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
