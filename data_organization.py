import copy
import glob
import os, sys, shutil
from pathlib import Path
import json
import csv
import pandas as pd
import glob
from Bio import SeqIO
import gzip
import argparse

ACCEPTED_EXTENTIONS = [".bam", ".fastq", ".fastq.bz2", ".sam", ".gz", "fastq.bz", "fastq.bz.md5", ".cram", ".bam.cip",
                       ".bam.crypt"]
POTENTIAL_DELIMETERS = [".", "-", "_"]
ID_PREFIXES = ["EGAR", "EGAF", "EGAD", "EGAX"]
REF_TABLE = "EBI_consolidated_test.txt"
ON_SITE_TABLE = "McGill_onsite_filelist.details.csv"
SOURCE_DIR = ""
DEST_DIR = "/ihec_data"

#TODO Connect DRX and DRR IDs using the upper directory (AMED-Crest)
#TODO Figure out how to link CEMT IDs to IHEC IDs


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
    assert (os.path.isdir(args.destination_dir)), "Destination directory file not found"

    # first step: optional, update ref table from ebi website (keep old version)
    # Second step: search


def fetch_id(filename, missing_list):
    retval = ""
    for prefix in ID_PREFIXES:
        idx = filename.find(prefix)
        if idx != -1:  # if prefix is found
            retval = filename[idx:idx + 15]
            break
    onsite_list = pd.read_csv(ON_SITE_TABLE)
    for row in onsite_list:
        fn = row[4]  # where the file name is stored
        if fn in filename or filename in fn:  # if one filename contains another
            retval = row[1]  # return EGAX id
            break
    if not retval:  # if retval is empty
        missing_list.append(filename)
    return retval, missing_list


def scan_through(ref_list):  # Scans through source directory and moves stuff around
    move_list = []
    rejected_extensions = []
    missing_list = []
    for elem_str in os.listdir():
        elem = Path(elem_str)
        if os.path.isfile(elem) and is_datafile(elem_str):
            print("elem is file", elem, elem_str)
            misc_id, missing_list = fetch_id(elem_str, missing_list)  # get the EGAX/etc id from the filename or the onsite list
            if misc_id:  # if there is a match for secondary id
                ihec_ids = match_to_db(misc_id, ref_list)  # list of ihec ids in which this file appears
                earliest_id = ihec_ids.pop(0)
                file_path = DEST_DIR + "/" + str(earliest_id[0:14]) + "/" + str(earliest_id)
                if not os.path.exists(file_path):  # if path does not already exist
                    os.mkdir(file_path)
                # shutil.move(str(os.getcwd()+elem), path)  # Uncomment when ready to move files

                # make symlinks for the rest of the occurrences:
                if ihec_ids:  # if there are later versions this file appears in, make symlinks to data file
                    for id in ihec_ids:
                        sym_path = DEST_DIR + "/" + str(id[0:14]) + "/" + str(id)
                        if not os.path.exists(sym_path):  # if path does not already exist
                            os.mkdir(sym_path)
                        os.symlink(file_path, sym_path)
                        # perhaps above should be os.symlink(file_path + "/" + elem, sym_path)?
                move_list.append(
                    {
                        "source location": str(os.getcwd()) + "/" + elem_str,
                        "destination": file_path,
                        "other versions": ihec_ids
                    }
                )
        elif os.path.isdir(elem):
            print(elem, "is directory!")
            saved_wd = os.getcwd()
            new_wd = os.path.join(saved_wd, elem)
            os.chdir(new_wd)
            scan_through(ref_list)
            os.chdir(saved_wd)
        else:
            rejected = elem_str.split(".")[-1]  # save extensions that are on disc that are not in accpeted list
            if rejected not in rejected_extensions:
                rejected_extensions.append(rejected)
    #print(rejected_extensions)
    return move_list


'''
def get_id(filename):
    for char in POTENTIAL_DELIMETERS:
        filename = filename.split(char).pop(0)
    return filename
'''


def is_datafile(filename):
    for ext in ACCEPTED_EXTENTIONS:
        if filename.endswith(ext):
            return True
    return False


def match_to_db(misc_id, ref_list):
    ihec_ids = []
    for elem in ref_list["data"]:
        for inst in elem["instances"]:
            if inst["primary_id"] == misc_id or inst["secondary_id"] == misc_id \
                    or misc_id in inst["egar_id"] or misc_id in inst["egaf_id"]:
                ihec_ids.append(elem["ihec_id"])
    ihec_ids.sort()
    return ihec_ids

def path_string(path):
    path = path.split("/")
    new_path = path.pop(0)
    while path:
        new_path = new_path + '//' + path.pop(0)
    print(new_path)
    return new_path




args = parse_args()
check_args(args)

# I know it's bad practice to change global variables, but they need to reflect the args,
#   and the args need to be global, else they would be passed through 2-3 functions
REF_TABLE = args.ref_dir + '/' + REF_TABLE
ON_SITE_TABLE = args.ref_dir + '/' + ON_SITE_TABLE
SOURCE_DIR = args.source_dir + '/' + SOURCE_DIR
DEST_DIR = args.destination_dir


REF_TABLE = path_string(REF_TABLE)
with open(REF_TABLE) as rt:
    os.chdir(args.source_dir)
    ref_table = json.load(rt)
    move_list = scan_through(ref_table)
    move_list = json.dumps(move_list, indent=2)
    print(move_list)
