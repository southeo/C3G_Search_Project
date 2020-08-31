import csv
import hashlib
import os

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
    print("Hash is same:", hash1 == hash2, '\t', filename)
    return hash1 == hash2



with open("Duplicate_list_all.txt") as dup, open("False_dups_time_check.txt", "r+") as fd:
    dup_reader = csv.reader(dup, delimiter=',')
    writer = csv.writer(fd)
    for row in dup_reader:
        file1 = os.path.join(row[1], row[0])
        file2 = row[2]
        if not is_same_hash(file1, file2):
            new_row = [file1, file2]
            writer.writerow(new_row)
            print("ROW ADDED: ", row)





