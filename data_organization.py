
import os, sys, shutil
from pathlib import Path
import json
import csv
import hashlib
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, date

ACCEPTED_EXTENSIONS = [".bam", ".fastq", ".fastq.bz2", ".sam", ".gz", "fastq.bz", "fastq.bz.md5", ".cram", ".cip",
                       ".crypt", ".bcf", ".md5", "vcf"]
POTENTIAL_DELIMETERS = [".", "-", "_"]
ID_PREFIXES = ["EGAR", "EGAF", "EGAD", "EGAX", "DRX"]
REF_TABLE = ""
JGAD_DIR = "JGAD_metadata"
ON_SITE_TABLE = "McGill_onsite_filelist.details.csv"
SOURCE_DIR = ""
DEST_DIR = "IHEC_Data_Home"
DEST_DIR_EXTRA = "Extra_files"
DEST_DIR_METADATA = "Metadata/Archived_Metadata"
METADATA_EXENSIONS = [".csv", ".txt", ".json", ".xml"]
MISSING_LIST = "No_Misc_ID_List.txt"
REJECTED_LIST = "Rejected_file_list_1.txt"
DUPLICATE_LIST = "Duplicate_list_all.txt"
MOVE_FILES = False
FALSE_DUPLICATES = []
ONSITE_LIST = "Onsite_Files_" + str(date.today())
EXTRA_DIR_LIST = ["EGA", "ENCODE", "GEO", "BLUEPRINT", "KNIH", "CEEHRC", "DEEP", "AMED-CREST", "GIS", "ASPERA",
                  "CEMT", "EPIVAR"]

## Argument Parsing and Setup

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
    parser.add_argument('-m',
                        "--move_files",
                        help="Enter True to move files (otherwise just generates report)",
                        required=False)
    return parser.parse_args()


def check_args(args):
    # make sure directories exist
    assert (os.path.isdir(args.source_dir)), "Source directory not found"
    assert (os.path.isdir(args.destination_dir)), "Destination directory not found"
    assert (os.path.isdir(args.ref_dir)), "Reference file directory not found"


def get_ref_table(ref_dir):  # looks for most up to-date metadata file
    latest = date.min
    latest_file = ""
    for elem in os.listdir(ref_dir):
        if "EBI_Database_Consolidated_" in elem:
            date_str = elem.replace("EBI_Database_Consolidated_", "")
            date_str = date_str[0:10]
            date_str = datetime.strptime(date_str, '%Y-%m-%d').date()
            if not latest_file:
                latest_file = elem
                latest = date_str
            elif date_str > latest:
                latest = date_str
                latest_file = elem
    return latest_file


## Get Secondary IDs

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


def fetch_egaf_id(filepath):
    idx = filepath.find("EGAF")
    if idx != -1:  # if prefix is found
        return filepath[idx:idx + 15]
    return ""


def key_match(id, inst):
    if (inst["primary_id"] is not None and inst["primary_id"] == id) or \
            (inst["secondary_id"] is not None and inst["secondary_id"] == id) \
            or ("egaf_id" in inst.keys() and id in inst["egaf_id"]) \
            or ("egar_id" in inst.keys() and id in inst["egar_id"]) \
            or ("local_ids" in inst.keys() and id in inst["local_ids"]):
        return True
    return False


def get_local_ids(ihec_id, local_id, ref_list):
    for entry in ref_list["data"]:
        if entry["ihec_id"] == ihec_id:
            for inst in entry["instances"]:
                if "local_ids" in inst.keys():
                    return inst["local_ids"]


def get_sub_dir():
    dir_str = str(os.getcwd()).casefold()
    for dir in EXTRA_DIR_LIST:
        if dir.casefold() in dir_str:
            return dir
    return "Other"


def fetch_id(filename, ref_list):
    retval = ""
    for prefix in ID_PREFIXES:
        idx = filename.find(prefix)
        if idx != -1:  # if prefix is found
            retval = filename[idx:idx + 15]
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
    else:  # Take primary id, not misc id
        for elem in ref_list["data"]:
            for inst in elem["instances"]:
                if "local_ids" in inst.keys():
                    if retval in inst["local_ids"]:
                        retval = inst["primary_id"]
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
    with open(path1, 'rb') as p1, open(path2, 'rb') as p2:
        hash1 = hash_bytestr_iter(file_as_blockiter(p1), hashlib.sha256())
        hash2 = hash_bytestr_iter(file_as_blockiter(p2), hashlib.sha256())
        return hash1 == hash2


def id_false_duplicates():
    with open(os.path.join(args.ref_dir,"False_dups.txt")) as fd:
        listreader = csv.reader(fd, delimiter='\n')
        for item in listreader:
            FALSE_DUPLICATES.append(item)


def move_false_duplicates(elem, local_ids, fp, file_path, ihec_ids):
    move_list.append({
        "source location": fp,
        "destination": file_path,
        "other versions": ihec_ids,
        "move_type": "data file, duplicate name",
        "file_name": str(elem),
        "local_ids": local_ids

    })
    if MOVE_FILES:
        copy = 1
        while os.path.exists(fp):
            os.rename(elem, str(elem) + "-" + str(copy))
            fp = os.path.join(file_path, elem)
            copy += 1  # Increment copy number until you have a unique name
        shutil.copyfile(elem, file_path)


## Moving files

def get_assay(ref_list, primary_id):
    for elem in ref_list["data"]:
        for inst in elem["instances"]:
            if primary_id == inst["primary_id"]:
                assay = inst["assay_type"]
                if assay == "RNA-Seq" or assay == "miRNA-Seq" or assay == "ncRNA-Seq": return "RNA-seq"
                if assay == "OTHER": return "Other"
                return assay
    return "Other"



def move_files(ihec_ids, elem, move_list, misc_id, ref_list):
    for id in ihec_ids:
        file_path = os.path.join(DEST_DIR, str(id[0:14]))
        # make directories:
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        file_path = os.path.join(file_path, id)
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        file_path = os.path.join(file_path, get_assay(ref_list, misc_id))
        if not os.path.exists(file_path):
            os.mkdir(file_path)
        # path including file name
        file_path = os.path.join(file_path, str(elem))
        src_path = os.path.abspath(elem)
        if not os.path.exists(file_path):
            # Move file to its new home
            if MOVE_FILES:
                try:
                    os.symlink(src_path, file_path)
                except FileExistsError:
                    pass
            local_ids = get_local_ids(id, misc_id, ref_list)
            move_list.append({
                "source location": src_path,
                "destination": file_path,
                "other versions": ihec_ids,
                "move_type": "data file",
                "file_name": str(elem),
                "local_ids": local_ids
                })
    return move_list


def move_extras(sub_dir, elem, misc_id):
    if not sub_dir:
        sub_dir = "Other"
    if not os.path.exists(DEST_DIR_EXTRA): os.mkdir(DEST_DIR_EXTRA)

    extra_path = os.path.join(DEST_DIR_EXTRA, sub_dir)
    if not os.path.exists(extra_path): os.mkdir(extra_path)
    if misc_id:
        extra_path = os.path.join(extra_path, misc_id)
    if not os.path.exists(extra_path): os.mkdir(extra_path)

    src_path = str(os.path.abspath(elem))
    if MOVE_FILES:
        try:
            os.symlink(src_path, str(os.path.join(extra_path, elem)))
        except FileExistsError:
            pass
    move_list.append({
        "source location": str(os.getcwd()) + "/" + str(elem),
        "destination": extra_path,
        "other versions": "N/A",
        "move type": "extra file",
        "file_name": str(elem)
    })
    return move_list


def move_metadata(elem, move_list, ref_list):
    if not os.path.exists(DEST_DIR_METADATA):
        os.mkdir(DEST_DIR_METADATA)
    misc_id = fetch_id(elem, ref_list)
    if misc_id:
        md_path = os.path.join(DEST_DIR_METADATA, misc_id)
    else:
        md_path = DEST_DIR_METADATA
    src_path = str(os.path.abspath(elem))
    if not os.path.exists(md_path):
        os.mkdir(md_path)
    if MOVE_FILES:
        try:
            os.symlink(src_path, os.path.join(md_path, elem))
        except FileExistsError:
            pass
    move_list.append({
        "source location": str(os.getcwd()) + "/" + elem,
        "destination": md_path,
        "other versions": "N/A",
        "move type": "metadata file",
        "file_name": str(elem)
    })
    return move_list


def fetch_primary_id(misc_id, ref_list):
    for elem in ref_list["data"]:
        for inst in elem["instances"]:
            if key_match(misc_id, inst):
                print(inst["primary_id"])
                return inst["primary_id"]
    print("rejected id: ", misc_id)
    return False


def scan_through(ref_list, move_list):  # Scans through source directory and moves stuff around
    missing_list = []
    for elem_str in os.listdir():
        elem = Path(elem_str)
        ihec_ids = []
        primary_id = ""
        #print('\t Current element:', elem)
        if os.path.isfile(elem) and is_datafile(elem_str):
            misc_id = fetch_id(elem_str, ref_list)  # get primary id from the filename, parent directory, or onsite list
            primary_id = fetch_primary_id(misc_id, ref_list)
            if primary_id:  # if there is a match for secondary id
                ihec_ids = match_to_db(primary_id, ref_list)  # list of ihec ids in which this file appears
                if ihec_ids:  # if there is a match between primary/secondary id and one or more ihec ids
                    move_list = move_files(ihec_ids, elem, move_list, primary_id, ref_list)
                    update_filename(ref_list, elem_str, primary_id, ihec_ids)
            else:  # If there is no match between ids, move the file into the extra file sub directory
                with open(REJECTED_LIST, "a+", newline="") as rj_lst:
                    # Write to Rejected list:
                    row = [elem, primary_id, "", "no corresponding IHEC ID", os.getcwd()]
                    writer = csv.writer(rj_lst)
                    writer.writerow(row)
                sub_dir = get_sub_dir()
                move_list = move_extras(sub_dir, elem, primary_id)
        elif os.path.isdir(elem):  # Recursively enter directories
            saved_wd = os.getcwd()
            new_wd = os.path.join(saved_wd, elem)
            os.chdir(new_wd)
            #print("Current directory: ", os.getcwd())
            move_list = scan_through(ref_list, move_list)
            os.chdir(saved_wd)
        elif is_metadatafile(elem_str):
            move_list = move_metadata(elem_str, move_list, ref_list)
        else:  # If elem is not a directory or appropriate file, add it to the rejected list
            rejected_ext = elem_str.split(".")[-1]  # save extensions that are on disc that are not in accpeted list
            with open(REJECTED_LIST, "a+", newline="") as rj_lst:
                row = [elem, "", rejected_ext, "Incorrect file type", os.getcwd()]
                writer = csv.writer(rj_lst)
                writer.writerow(row)
    return move_list


def update_filename(ref_list, filename, primary_id, ihec_ids):
    with open(ONSITE_LIST, "a+") as sl:
        for id in ihec_ids:
            src_path = os.path.abspath(filename)
            dest_path = os.path.join(DEST_DIR, id[0:14], id, get_assay(ref_list, primary_id))
            writer = csv.writer(sl)
            row = [filename, primary_id, id, src_path, dest_path]
            writer.writerow(row)


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
                    ("egaf_id" in inst.keys() and misc_id in inst['egaf_id']) or \
                    ("local_ids" in inst.keys() and misc_id in inst["local_ids"]):
                ihec_ids.append(elem["ihec_id"])
    ihec_ids.sort()
    return ihec_ids


def map_onsite_files(ref_table):
    with open(ref_table) as rt, open("Onsite_Files_" + str(date.today()), "a+") as sl:
        ebi_table = json.load(rt)
        writer = csv.writer(sl)
        header = ["File_Name", "IHEC_ID", "Primary_ID", "Location"]
        writer.writerow(header)

        for elem in ebi_table["data"]:
            for inst in elem["instances"]:
                if "filename" in inst.keys():
                    for file in inst["filename"]:
                        row = file[0], elem["ihec_id"], inst["primary_id"], \
                              "/Epigenetic_Data_Home/" + elem["ihec_id"][0:14] + '/' + elem["ihec_id"] + '/' + file[0]
                        writer.writerow(row)


args = parse_args()
check_args(args)

os.chdir(args.ref_dir)
SOURCE_DIR = os.path.abspath(args.source_dir)
DEST_DIR = os.path.abspath(args.destination_dir)
DEST_DIR_EXTRA = os.path.abspath(os.path.join(args.destination_dir, DEST_DIR_EXTRA))
DEST_DIR_METADATA = os.path.abspath(os.path.join(args.destination_dir, DEST_DIR_METADATA))
REF_TABLE = os.path.abspath(os.path.join(args.ref_dir, get_ref_table(args.ref_dir)))
REF_TABLE = "EBI_Consolidated_test.txt"
ON_SITE_TABLE = os.path.abspath(os.path.join(args.ref_dir, ON_SITE_TABLE))
MISSING_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, MISSING_LIST)))
REJECTED_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, REJECTED_LIST)))
DUPLICATE_LIST = Path(os.path.abspath(os.path.join(args.ref_dir, DUPLICATE_LIST)))
JGAD_DIR = Path(os.path.abspath(os.path.join(args.ref_dir, JGAD_DIR)))
if args.move_files:
    MOVE_FILES = args.move_files
id_false_duplicates()
ONSITE_LIST = os.path.abspath(os.path.join(args.ref_dir, ONSITE_LIST)) + "_fixed"
with open(REF_TABLE) as rt, open("Move_List_3.txt", 'w+') as mv_lst:
    ref_list = json.load(rt)
    os.chdir(args.source_dir)
    move_list = []
    move_list = scan_through(ref_list, move_list)
    json.dump(move_list, mv_lst, indent=2)
