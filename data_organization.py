'''import copy
import glob
import os, sys
import pathlib
import json
import csv
import pandas as pd
import glob

ACCEPTED_EXTENTIONS = [".bam", ".fastq", ".fastq.bz2", ".sam", ".gz", "fastq.bz", "fastq.bz.md5", ".cram", ".bam.cip",
					   ".bam.crypt"]
# cip is encoded .bam file
# Ask hector
# if there is only .cip and no bam, flag it
POTENTIAL_DELIMETERS = [".", "-", "_"]


def scan_through(ref_list):
	for elem in os.listdir():
		if os.path.isfile(elem) and is_datafile(elem):
			id = get_id(elem)  # get first characters before extentions/extra information
			ref_list = match_to_db(id, ref_list)
			# print("original: ", str(elem), "  id:", id)
			match_to_db(id, ref_list)
		elif os.path.isdir(elem):
			saved_wd = os.getcwd()
			new_wd = os.path.join(saved_wd, elem)
			os.chdir(new_wd)
			# print("Dir: ", new_wd)
			scan_through(ref_list)
			os.chdir(saved_wd)


def get_id(filename):
	for char in POTENTIAL_DELIMETERS:
		filename = filename.split(char).pop(0)
	return filename


def is_datafile(filename):
	for ext in ACCEPTED_EXTENTIONS:
		if filename.endswith(ext):
			return True
	return False


def match_to_db(id, ref_list):
	for elem in ref_list["data"]:
		for inst in elem["instances"]:
			if inst["primary_id"] == id or inst["secondary_id"] == id:  # may need to be handled separately
				elem["instances"].pop(elem["instances"].index(inst))
				return
			if len(elem["instances"]) == 0:
				del elem
	return ref_list


''''''
print("Hello world!")
with open("EBI_Database_Consolidated_2020-07-06.txt") as rt:
	ref_table = json.load(rt)
	ref_table_copy = copy.deepcopy(ref_table)
	os.chdir("/genfs/projects/IHEC/jbodpool_mp2/")
	scan_through(ref_table_copy)
	count = 0
	for elem in ref_table_copy["data"]:
		#print("ID: ", elem["ihec_id"], ", Project: ", elem["project"])
		count +=1
	print("number not downloaded: ", count, ", ", count/len(ref_table)*100,"%")    '''

'''def get_ihec_list(ref_table):
	primary_ids = []
	for elem in ref_table["data"]:
		for inst in elem["instances"]:
			primary_ids.append(inst["primary_id"])
	return primary_ids


with open("EBI_Database_Consolidated_2020-07-06.txt") as rt:
	ref_table = json.load(rt)
	onsite_list = pd.read_csv("McGill_onsite_filelist.details.csv")

	on_disc_on_ebi = []
	not_disc_on_ebi = []
	on_disc_not_on_ebi = []

	ihec_list = get_ihec_list(ref_table)
	os.chdir('../../../jbodpool_mp2')
	for id in onsite_list["EXPERIMENT_ACCESSION"]:
		# print(id)
		if id in ihec_list:
			on_disc_on_ebi.append(id)
			path = str(id) + "/*"
			print("globbing: ", path, ", ", glob.glob(path))
			#print(path)
		elif str(id) != "nan":
			on_disc_not_on_ebi.append(id)
			#print(id)

	for id in ihec_list:
		if id not in onsite_list and "EGAX" in str(id):
			not_disc_on_ebi.append(id)
			#print(id)
		else:
			pass
			#print(id)


	#print("On disc and EBI: ", len(on_disc_on_ebi), ", ", len(on_disc_on_ebi) / len(onsite_list),
	#	  "%, \n On disc and not on EBI: ", len(on_disc_not_on_ebi), ", ", len(on_disc_not_on_ebi) / len(onsite_list),
	#	"%, \n Not disc and on EBI: ", len(not_disc_on_ebi), ", ", len(not_disc_on_ebi) / len(ihec_list))

# not_downloaded = json.dumps(ref_table_copy, indent=4)
#    print(not_downloaded)
'''


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
HOME_DIR = "/ihec_data"
REF_TABLE = "EBI_Database_Consolidated_2020-07-06.txt"
ON_SITE_TABLE = "McGill_onsite_filelist.details.csv"

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
                        '--ref_table',
                        help="Reference table from EBI site",
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


def scan_through(ref_list, dest_dir):
    move_list = []
    rejected_extensions = []
    missing_list = []
    for elem_str in os.listdir():
        elem = Path(elem_str)
        if os.path.isfile(elem) and is_datafile(elem_str):
            print("elem is file")
            misc_id, missing_list = fetch_id(elem_str, missing_list)  # get the EGAX/etc id from the filename or the onsite list
            if misc_id:  # if there is a match for secondary id
                ihec_ids = match_to_db(misc_id, ref_list)  # list of ihec ids in which this file appears
                earliest_id = ihec_ids.pop(0)
                file_path = dest_dir + "/" + str(earliest_id[0:14]) + "/" + str(earliest_id)
                if not os.path.exists(file_path):  # if path does not already exist
                    os.mkdir(file_path)
                # shutil.move(str(os.getcwd()+elem), path)  # Uncomment when ready to move files

                # make symlinks for the rest of the occurrences:
                if ihec_ids:  # if there are later versions this file appears in, make symlinks to data file
                    for id in ihec_ids:
                        sym_path = dest_dir + "/" + str(id[0:14]) + "/" + str(id)
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


args = parse_args()
check_args(args)

with open(args.ref_table) as rt:
    os.chdir(args.source_dir)
    ref_table = json.load(rt)
    move_list = scan_through(ref_table, args.destination_dir)
    move_list = json.dumps(move_list, indent=2)
    print(move_list)
