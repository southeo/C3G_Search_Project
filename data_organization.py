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
import xml.etree.ElementTree as ET



ACCEPTED_EXTENTIONS = [".bam", ".fastq", ".fastq.bz2", ".sam", ".gz", "fastq.bz", "fastq.bz.md5", ".cram", ".cip",
                       ".crypt", ".bcf"]
POTENTIAL_DELIMETERS = [".", "-", "_"]
ID_PREFIXES = ["EGAR", "EGAF", "EGAD", "EGAX", "DRX"]
REF_TABLE = "EBI_Consolidated_test.txt"
JGAD_DIR = "JGAD_metadata"
ON_SITE_TABLE = "McGill_onsite_filelist.details.csv"
SOURCE_DIR = ""
DEST_DIR = ""
MISSING_LIST = "No_Misc_ID_List.txt"
REJECTED_LIST = "Rejected_file_list.txt"

# TODO Figure out how to link CEMT IDs to IHEC IDs


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


def get_JGAR_id(dir_name):
    JGAD_id = str(Path(dir_name).parent).split("/")[-1]
    md_file = ""
    for elem in os.listdir(JGAD_DIR):
        if JGAD_id in elem:
            md_file = elem
            break
    md_file = os.path.join(JGAD_DIR, md_file)
    tree = ET.parse(md_file)
    root = tree.getroot()
    for alias in root.iter("alias"):
        print(alias.attrib)
    '''
    blah blah blah parse JGAD tree and return its 
    '''


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
            retval = get_JGAR_id(working_dir)
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


def scan_through(ref_list, move_list):  # Scans through source directory and moves stuff around
    rejected_extensions = []
    missing_list = []
    for elem_str in os.listdir():
        elem = Path(elem_str)
        ihec_ids = []
        if os.path.isfile(elem) and is_datafile(elem_str):
            misc_id = fetch_id(elem_str)  # get the EGAX/etc id from the filename or the onsite list
            if misc_id:  # if there is a match for secondary id
                ihec_ids = match_to_db(misc_id, ref_list)  # list of ihec ids in which this file appears
                if ihec_ids:
                    first_id = ihec_ids.pop(0)
                    file_path = os.path.join(DEST_DIR, str(first_id[0:14]))
                    # print(file_path)
                    try:
                        os.mkdir(file_path)
                        file_path = os.path.join(file_path, first_id)
                        os.mkdir(file_path)
                    except FileExistsError:
                        try:
                            file_path = os.path.join(file_path, first_id)
                            os.mkdir(file_path)
                        except FileExistsError:
                            # print(file_path, "already exists")
                            pass
                    # shutil.move(elem, file_path)  # Uncomment when ready to move files
                    # make symlinks for the rest of the occurrences:
                    if ihec_ids:  # if there are later versions this file appears in, make symlinks to data file for each subsequent ihec id
                        for id in ihec_ids:
                            sym_path = os.path.join(DEST_DIR, str(id[0:14]))
                            try:
                                os.mkdir(sym_path)
                                file_path = os.path.join(sym_path, id)
                                os.mkdir(sym_path)
                            except FileExistsError:
                                try:
                                    sym_path = os.path.join(sym_path, id)
                                    os.mkdir(sym_path)
                                    # print(elem, "symlink occurs in ", sym_path)
                                except FileExistsError:
                                    # print(sym_path, "already exists")
                                    pass
                        # os.symlink((os.path.join(file_path, filename), sym_path)
                    move_list.append({
                        "source location": str(os.getcwd()) + "/" + elem_str,
                        "destination": file_path,
                        "other versions": ihec_ids
                    })
        elif os.path.isdir(elem):
            saved_wd = os.getcwd()
            new_wd = os.path.join(saved_wd, elem)
            os.chdir(new_wd)
            move_list = scan_through(ref_list, move_list)
            os.chdir(saved_wd)
        else:
            #rejected = elem_str.split(".")[-1]  # save extensions that are on disc that are not in accpeted list
            #if rejected not in rejected_extensions:
            with open(REJECTED_LIST, "a+", newline="") as rj_lst:
                row = [elem]
                writer = csv.writer(rj_lst)
                writer.writerow(row)
    # print(rejected_extensions)
    return move_list


def is_datafile(filename):
    for ext in ACCEPTED_EXTENTIONS:
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

# I know it's bad practice to change global variables, but they need to reflect the args,
#   and the args need to be global, else they would be passed through 2-3 functions
os.chdir(args.ref_dir)
SOURCE_DIR = os.path.abspath(args.source_dir)
DEST_DIR = os.path.abspath(args.destination_dir)
REF_TABLE = os.path.abspath(os.path.join(args.ref_dir, REF_TABLE))
ON_SITE_TABLE = os.path.abspath(os.path.join(args.ref_dir, ON_SITE_TABLE))
MISSING_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, MISSING_LIST)))
REJECTED_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, REJECTED_LIST)))
JGAD_DIR = Path(os.path.abspath(os.path.join(args.ref_dir, JGAD_DIR)))

# print("source: ", SOURCE_DIR, '\n dest: ', DEST_DIR, "\n ref table: ", REF_TABLE, '\n on site table:', ON_SITE_TABLE)
with open(REF_TABLE) as rt, open("Move_List.txt", 'w') as mv_lst:
    os.chdir(args.source_dir)
    ref_table = json.load(rt)
    move_list = []
    move_list = scan_through(ref_table, move_list)
    json.dump(move_list, mv_lst, indent=2)
