import copy
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


'''
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


def get_ihec_list(ref_table):
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

	for id in onsite_list["EXPERIMENT_ACCESSION"]:
		# print(id)
		if id in ihec_list:
			on_disc_on_ebi.append(id)
			path = "*/" + str(id)
			print(glob.glob(path))
		elif str(id) != "nan":
			on_disc_not_on_ebi.append(id)
			print(id)

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
