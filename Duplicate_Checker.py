import csv
import hashlib
import os
import multiprocessing as mp

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


def is_same_hash(path1, path2):
    hash1 = hash_bytestr_iter(file_as_blockiter(open(path1, 'rb')), hashlib.sha256())
    hash2 = hash_bytestr_iter(file_as_blockiter(open(path2, 'rb')), hashlib.sha256())
    filename = path2.split('/')[-1]
    dup_reader = csv.reader(dup, delimiter=',')
    if hash1 != hash2:
        file = path1.split('/')[-1]
        new_row = [file, path1, path2]
        output.put(new_row)


with open("Duplicate_list_all.txt") as dup:
    dup_csv_reader = csv.reader(dup)
    dup_list1 = []
    dup_list2 = []
    for row in dup_csv_reader:
        dup_list1.append(os.path.join(row[1], row[0]))
        dup_list1.append(row[2])

pool = mp.Pool(mp.cpu_count())
output = mp.Queue()
processes = [mp.Process(target=is_same_hash, args=(dup_list1, dup_list2)) for dup1, dup2 in zip(dup_list1, dup_list2)]

for p in processes:
    p.start()

for p in processes:
    p.join()

results = [output.get() for p in processes]
print(results)


