import csv
import hashlib
import os
from pathlib import Path
import multiprocessing as mp
import timeit

def hash_bytestr_iter(bytesiter, hasher, ashexstr=False):
    for block in bytesiter:
        hasher.update(block)
    return hasher.hexdigest() if ashexstr else hasher.digest()


def file_as_blockiter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)


def is_same_hash(paths):  #, output): #time benchmark, mem benchmark
    with open(paths[0], 'rb') as p1, open(paths[1], 'rb') as p2:
        hash1 = hash_bytestr_iter(file_as_blockiter(p1), hashlib.sha256())
        hash2 = hash_bytestr_iter(file_as_blockiter(p2), hashlib.sha256())
        filename = paths[0].split('/')[-1]
        if hash1 != hash2:
            new_row = [filename, paths[0], paths[1]]
            return new_row


if __name__ == '__main__':
    with open("Duplicate_list_all.txt") as dup:
        dup_csv_reader = csv.reader(dup)
        dup_list = []
        # dup_list1 = []
        # dup_list2 = []
        for row in dup_csv_reader:
            # dup_list1.append(os.path.join(row[1], row[0]))
            # dup_list2.append(row[2])
            p1 = os.path.join(Path(row[1]), Path(row[0]))
            p2 = row[2]
            dup_list.append((p1, p2))  # append a tuple

    pool = mp.Pool(mp.cpu_count())
    output = pool.map(is_same_hash, dup_list)
    print("Output: {}".format(output))
'''
pool = mp.Pool(mp.cpu_count())
output = mp.Queue()


results = [pool.apply_async(is_same_hash, args=(dup1, dup2, output)) for dup1, dup2 in zip(dup_list1, dup_list2)]
output = [p.get() for p in results]
print(output)


processes = [mp.Process(target=is_same_hash, args=(dup1, dup2)) for dup1, dup2 in zip(dup_list1, dup_list2)]\
for p in processes:
    p.start()

for p in processes:
    p.join()

results = [output.get() for p in processes]
print(results)
'''
