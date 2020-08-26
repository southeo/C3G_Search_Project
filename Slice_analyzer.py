import json
import csv
import os
import xml.etree.ElementTree as ET
from pathlib import Path

ID_PREFIXES = ["EGAR", "EGAF", "EGAD", "EGAX", "DRX"]
ON_SITE_TABLE = "McGill_onsite_filelist.details.csv"
JGAD_DIR = "JGAD_metadata"


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
    return retval

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

with open("Slice_files.txt", "r") as slice_list, open("Move_List_2.txt") as mv_list:
    move_list = json.load(mv_list)
    slice_list_reader = csv.reader(slice_list, delimiter=',')
    for row in slice_list_reader:
        slice_file = row[0]
        '''
        slice_id = fetch_id(slice_file)
        for file in move_list:
            file_id = fetch_id(file)
            if slice_id in file_id or file_id in slice_id:
                print(slice_id) '''






