import copy
import glob
import os, sys, shutil
from pathlib import Path
import json
import csv
import pandas as pd
import glob
import gzip
import hashlib
import argparse
import xml.etree.ElementTree as ET

ACCEPTED_EXTENSIONS = [".bam", ".fastq", ".fastq.bz2", ".sam", ".gz", "fastq.bz", "fastq.bz.md5", ".cram", ".cip",
                       ".crypt", ".bcf", ".md5", "vcf"]
POTENTIAL_DELIMETERS = [".", "-", "_"]
ID_PREFIXES = ["EGAR", "EGAF", "EGAD", "EGAX", "DRX"]
REF_TABLE = "EBI_Consolidated_test.txt"
SLICE_FILES_LIST = "Slice_files.txt"
JGAD_DIR = "JGAD_metadata"
ON_SITE_TABLE = "McGill_onsite_filelist.details.csv"
SOURCE_DIR = ""
DEST_DIR = ""
DEST_DIR_EXTRA = "Extra_files"
DEST_DIR_METADATA = "Archived_metadata_files"
METADATA_EXENSIONS = [".csv", ".txt", ".json", ".xml"]
MISSING_LIST = "No_Misc_ID_List.txt"
REJECTED_LIST = "Rejected_file_list.txt"
DUPLICATE_LIST = "Duplicate_list.txt"
CONSORTIUM_LIST = ["BLUEPRINT", "AMED-CREST", "no_backup", "EpiVar", "pyega3"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s',
                        '--source_dir',
                        help="Root directory that contains data to be moved",
                        required=True)
    parser.add_argument('-d',
                        '--destination_dir',
                        help="Root directory that will hold organized data",
                        required=True)
    parser.add_argument('-r',
                        '--ref_dir',
                        help="Directory that holds reference files",
                        required=True)
    return parser.parse_args()


def check_args(args):
    # make sure directories exist
    assert (os.path.isdir(args.source_dir)), "Source directory not found"
    assert (os.path.isdir(args.destination_dir)), "Destination directory not found"
    assert (os.path.isdir(args.ref_dir)), "Reference file directory not found"


def get_JGAR_id(dir_name, filename):
    JGAD_id = str(Path(dir_name).parent).split("/")[-1]
    JGAR_id = str(Path(dir_name)).split("/")[-1]
    md_file = ""
    for elem in os.listdir(JGAD_DIR):
        if JGAD_id in elem:
            md_file = elem
            break
    md_file = os.path.join(JGAD_DIR, md_file)
    tree = ET.parse(md_file)
    root = tree.getroot()

    for elem in root.findall("DATA"):
        if JGAR_id == elem.get("alias"):
            for child in elem.findall("EXPERIMENT_REF"):
                JGAX_id = child.get("refname")
                return JGAX_id


def fetch_id(filename):
    retval = ""
    for prefix in ID_PREFIXES:
        idx = filename.find(prefix)
        if idx != -1:  # if prefix is found
            retval = filename[idx:idx + 15]
            # print(prefix, filename)
            break
    if "EGAZ" in filename:  # need to go through on-site list to get EGAX id
        with open(ON_SITE_TABLE) as onsite_csv:
            onsite_list = csv.reader(onsite_csv)
            next(onsite_list)
            for row in onsite_list:
                fn = row[2]  # where the file name is stored
                if "EGAZ" in fn and (fn in filename or filename in fn):  # if one filename contains another
                    retval = row[3]  # return EGAD id
                    break
    if not retval:  # if retval is STILL empty, check the directory name, not the file name
        working_dir = os.getcwd()
        if "JGAR" in working_dir:
            retval = get_JGAR_id(working_dir, filename)
        else:
            for prefix in ID_PREFIXES:
                idx = working_dir.find(prefix)
                if idx != -1:  # if prefix is found
                    retval = working_dir[idx:idx + 15]
                    break
    if not retval:  # if retval is STILL empty, write it to missing list. This will have no misc id associated with it
        with open(MISSING_LIST, "a+", newline="") as ms_lst:
            row = [filename, os.getcwd()]
            writer = csv.writer(ms_lst)
            writer.writerow(row)
    return retval


# Hash functions:
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
    return hash1 == hash2

def move_files(ihec_ids, elem, move_list):
    first_id = ihec_ids.pop(0)
    file_path = os.path.join(DEST_DIR, str(first_id[0:14]))
    # make directories:
    try:
        os.mkdir(file_path)
        file_path = os.path.join(file_path, first_id)
        os.mkdir(file_path)
    except FileExistsError:
        try:
            file_path = os.path.join(file_path, first_id)
            os.mkdir(file_path)
        except FileExistsError:
            pass
    # path including file name
    fp = os.path.join(file_path, str(elem))
    if not os.path.exists(fp):
        # Move file to its new home
        # shutil.copyfile(elem, file_path)

        # Duplicate checking -> only use when files have yet to be copied
        # Once files have been copied, you can check the file path directly, instead of referencing the move_list

        dup = False
        for item in move_list:
            if str(elem) == item["file_name"]:
                #print(elem, "\t", item["source location"])
                hash1 = hash_bytestr_iter(file_as_blockiter(open(elem, 'rb')), hashlib.sha256())
                hash2 = hash_bytestr_iter(file_as_blockiter(open(item["source location"], 'rb')), hashlib.sha256())
                #print("New File Hash: ", hash1)
                #print("Existing File Hash: ", hash2)
                if hash1 != hash2:
                   print("different hash, different files")
                with open(DUPLICATE_LIST, "a") as dp_lst:
                    row = [elem, file_path, os.getcwd()]
                    writer = csv.writer(dp_lst)
                    writer.writerow(row)
                    dup = True
        if not dup:
            move_list.append({
                "source location": str(os.getcwd()) + "/" + str(elem),
                "destination": file_path,
                "other versions": ihec_ids,
                "move_type": "data file",
                "file_name": str(elem)
            })
    elif not is_same_hash(fp, elem):  # If files are different but have same name
        move_list.append({
            "source location": fp,
            "destination": file_path,
            "other versions": ihec_ids,
            "move_type": "data file, duplicate name",
            "file_name": str(elem)
        })
        # TODO: get path of false duplicate files
        copy = 1
        while os.path.exists(fp):
            os.rename(elem, str(elem + "-" + copy))
            fp = os.path.join(file_path, elem)
            copy += 1  # Increment copy number until you have a unique name
        # shutil.copyfile(elem, file_path)

    # Create symlinks for files that appear in later IHEC versions
    for id in ihec_ids:
        sym_path = os.path.join(DEST_DIR, str(id[0:14]))
        try:
            os.mkdir(sym_path)
            sym_path = os.path.join(sym_path, id)
            os.mkdir(sym_path)
        except FileExistsError:
            try:
                sym_path = os.path.join(sym_path, id)
                os.mkdir(sym_path)
                # print(elem, "symlink occurs in ", sym_path)
            except FileExistsError:
                pass
        # Create symlink
        # os.symlink((os.path.join(file_path, elem), sym_path)

    return move_list


def get_sub_dir(elem):
    for sub_dir in CONSORTIUM_LIST:
        if sub_dir in str(os.path.abspath(elem)):
            return sub_dir
    return False


def move_extras(sub_dir, elem, misc_id):
    if sub_dir:
        extra_path = os.path.join(DEST_DIR_EXTRA, sub_dir)
        try:
            os.mkdir(extra_path)
            extra_path = os.path.join(extra_path, misc_id)
            os.mkdir(extra_path)
        except FileExistsError:
            try:
                extra_path = os.path.join(extra_path, misc_id)
                os.mkdir(extra_path)
            except FileExistsError:
                pass
        # shutil.copyfile(elem, extra_path)
        move_list.append({
            "source location": str(os.getcwd()) + "/" + str(elem),
            "destination": extra_path,
            "other versions": "N/A",
            "move type": "extra file",
            "file_name": str(elem)
        })
    return move_list


def move_metadata(elem, move_list):
    if not os.path.exists(DEST_DIR_METADATA):
        os.mkdir(DEST_DIR_METADATA)
    misc_id = fetch_id(elem)
    if misc_id:
        md_path = os.path.join(DEST_DIR, misc_id)
    else:
        md_path = DEST_DIR_METADATA
    # shutil.copyfile(elem, md_path)
    move_list.append({
        "source location": str(os.getcwd()) + "/" + elem,
        "destination": md_path,
        "other versions": "N/A",
        "move type": "metadata file",
        "file_name": str(elem)
    })
    return move_list


def scan_through(ref_list, move_list):  # Scans through source directory and moves stuff around
    missing_list = []
    for elem_str in os.listdir():
        elem = Path(elem_str)
        ihec_ids = []
        misc_id = []
        if os.path.isfile(elem) and is_datafile(elem_str):
            misc_id = fetch_id(elem_str)  # get primary/secondary id from the filename, parent directory, or onsite list
            if misc_id:  # if there is a match for secondary id
                ihec_ids = match_to_db(misc_id, ref_list)  # list of ihec ids in which this file appears
                if ihec_ids:  # if there is a match between primary/secondary id and one or more ihec ids
                    move_list = move_files(ihec_ids, elem, move_list)
                else:  # If there is no match between ids, move the file into the extra file sub directory
                    with open(REJECTED_LIST, "a+", newline="") as rj_lst:
                        # Write to Rejected list:
                        row = [elem, misc_id, "", "no corresponding IHEC ID", os.getcwd()]
                        writer = csv.writer(rj_lst)
                        writer.writerow(row)
                    sub_dir = get_sub_dir(elem)
                    move_list = move_extras(sub_dir, elem, misc_id)
        elif os.path.isdir(elem):  # Recursively enter directories
            saved_wd = os.getcwd()
            new_wd = os.path.join(saved_wd, elem)
            os.chdir(new_wd)
            move_list = scan_through(ref_list, move_list)
            os.chdir(saved_wd)
        elif is_metadatafile(elem_str):
            move_list = move_metadata(elem_str, move_list)
        elif elem_str.endswith(".slice"):  # Gather all slice files for analysis
            with open(SLICE_FILES_LIST, "a") as slice_list:
                row = [elem_str, os.getcwd()]
                writer = csv.writer(slice_list)
                writer.writerow(row)
                print(elem_str)
        else:  # If elem is not a directory or appropriate file, add it to the
            rejected_ext = elem_str.split(".")[-1]  # save extensions that are on disc that are not in accpeted list
            with open(REJECTED_LIST, "a+", newline="") as rj_lst:
                row = [elem, "", rejected_ext, "Incorrect file type", os.getcwd()]
                writer = csv.writer(rj_lst)
                writer.writerow(row)
    return move_list


def is_datafile(filename):
    for ext in ACCEPTED_EXTENSIONS:
        if filename.endswith(ext):
            return True
    return False


def is_metadatafile(filename):
    for ext in METADATA_EXENSIONS:
        if filename.endswith(ext):
            return True
    return False


def match_to_db(misc_id, ref_list):
    ihec_ids = []
    for elem in ref_list["data"]:
        for inst in elem["instances"]:
            if inst["primary_id"] == misc_id or inst["secondary_id"] == misc_id or \
                    ("egar_id" in inst.keys() and misc_id in inst['egar_id']) or \
                    ("egaf_id" in inst.keys() and misc_id in inst['egaf_id']):
                ihec_ids.append(elem["ihec_id"])
    ihec_ids.sort()
    return ihec_ids


args = parse_args()
check_args(args)

os.chdir(args.ref_dir)
SOURCE_DIR = os.path.abspath(args.source_dir)
DEST_DIR = os.path.abspath(args.destination_dir)
DEST_DIR_EXTRA = os.path.abspath(os.path.join(args.destination_dir, DEST_DIR_EXTRA))
DEST_DIR_METADATA = os.path.abspath(os.path.join(args.destination_dir, DEST_DIR_METADATA))
REF_TABLE = os.path.abspath(os.path.join(args.ref_dir, REF_TABLE))
ON_SITE_TABLE = os.path.abspath(os.path.join(args.ref_dir, ON_SITE_TABLE))
MISSING_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, MISSING_LIST)))
REJECTED_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, REJECTED_LIST)))
DUPLICATE_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, DUPLICATE_LIST)))
JGAD_DIR = Path(os.path.abspath(os.path.join(args.ref_dir, JGAD_DIR)))

# print("source: ", SOURCE_DIR, '\n dest: ', DEST_DIR, "\n ref table: ", REF_TABLE, '\n on site table:', ON_SITE_TABLE)

with open(REF_TABLE) as rt, open("Move_List.txt", 'w') as mv_lst:
    os.chdir(args.source_dir)
    ref_table = json.load(rt)
    move_list = []
    move_list = scan_through(ref_table, move_list)
    json.dump(move_list, mv_lst, indent=2)
