import csv
import glob
import sys
import argparse
import os
from os import path
import json
import copy
from datetime import datetime, date

INSTANCE_SEARCHES = ["primary_id", "secondary_id", "assay_type", "experiment_type",
                     "archive"]  # these searches are handled differently
KEYWORD_SEARCHES = ["donor_keyword_id", "disease_keywords", "donor_ethnicity_keywords", "tissue_keywords"]
ID_PREFIXES = ["EGAR", "EGAF", "EGAD", "EGAX"]
DUP_ID_LIST = []
OUTFILE = ""
ONSITE_LIST = ""


def help():
    print("********************************************************************************************************* \n"
          "Search Function Help \n"
          "********************************************************************************************************* \n"
          "Last updated: September 2, 2020 \n"
          "This program requires python 3.7.3 to run \n"
          "Compares user input to online EBI database and returns the location of the queried files on Beluga. \n "
          "A query file is one of two parameters passed into the search function. It is a tab-delimited text file file "
          "containing all information you are searching for. The first line of the file contains all seach "
          "parameters, and subsequent lines contain values to be matched. \n"
          "The reference file is the second parameter passed to the search function. It contains metadata for all "
          "datasets in the EBI database. It is named: \n EBI_Database_Consolidated_[Date of creation].txt \n"
          "for more information, visit [git repo]")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q',
                        '--query_table',
                        help="Text file containing search information",
                        required=True)
    parser.add_argument('-r',
                        '--ref_table',
                        help="Reference table from EBI site",
                        required=True)
    parser.add_argument('-o',
                        '--outfile',
                        help="Path to match output file (optional). ",
                        required=False)

    return parser.parse_args()


def check_args(args):
    # make sure files exist
    assert (os.path.isfile(args.query_table)), "Query table not found"
    assert (os.path.isfile(args.ref_table)), "Reference table file not found"


def get_search_list(query_table):
    # reads query table and collects search functions
    search_list = []
    for elem in next(query_table_csv):
        search_list.append(elem.casefold())
    return search_list


def match_search_params(scope, query, value):
    modified_scope = {"data": []}  # stores potential matches. This will limit the scope as searching progresses
    # print(query, ", ", type(query))
    for elem in scope["data"]:
        if query.casefold() in INSTANCE_SEARCHES:
            bad_matches = len(elem["instances"])
            # catch all bad matches. Loop through list of instances until certain there are none that sneak past
            while bad_matches > 0:
                bad_matches = len(elem["instances"])  # assume all items in this elem are bad
                for inst in elem["instances"]:
                    if value != str(inst[query]).casefold():  # remove all bad instance matches
                        elem["instances"].pop(elem["instances"].index(inst))
                    else:
                        bad_matches -= 1  # one less bad matc
            if elem["instances"]:  # if instance list is not empty
                modified_scope["data"].append(elem)  # Append only the results with the correct instance searches
        elif query == "age_min" and query in elem.keys():
            try:
                value = float(value)
            except ValueError:
                print("Invalid min age")
            if "age_min" in elem.keys() and value <= elem["age_min"]:
                modified_scope["data"].append(elem)
        elif query == "age_max":
            if query in elem.keys():
                try:
                    value = float(value)
                except ValueError:
                    print("Invalid max age")
                if "age_max" in elem.keys() and value >= elem["age_max"]:
                    modified_scope["data"].append(elem)
        elif query == "age_exact":
            if query in elem.keys():
                try:
                    value = float(value)
                except ValueError:
                    print("Invalid exact age")
                if "age_exact" in elem.keys() and value == elem["age_exact"]:
                    modified_scope["data"].append(elem)
        elif query.casefold() in KEYWORD_SEARCHES:
            # keyword searches: all items in input must be satisfied, but there may be extra keywords in the search element
            value_keywords = value.split()
            keywords_all_match = True
            for keyword in value_keywords:
                if keyword not in elem[query]:
                    keywords_all_match = False
            if keywords_all_match:
                modified_scope["data"].append(elem)
        elif query.casefold() == "ihec_id" and len(value) == 14:  # if no version is provided, provided latest version
            if elem["is live version?"] == "yes" and value == (str(elem[query]).casefold())[
                                                              0:14]:  # checks if it is latest
                modified_scope["data"].append(elem)
        else:
            if query in elem.keys() and value == str(elem[query]).casefold():
                modified_scope["data"].append(elem)
    return modified_scope


'''
def match_files(filename, elem):
    #References onsite file list and fetches primary id and inst
    with open(ONSITE_LIST, 'r') as ol:
        reader = csv.reader(ol)
        for row in reader:
            if row[0] == filename:
                pid = row[2]
                return pid
    return False
'''


def is_duplicate_pid(p_id, ref_list):
    # After this function checks for duplicate primary ids, it will save the list, so it only has to run this once
    primary_id_list = []
    if not DUP_ID_LIST:
        for elem in ref_list["data"]:
            for inst in elem["instances"]:
                PID = inst["primary_id"]
                if PID in primary_id_list:
                    DUP_ID_LIST.append(PID)
                else:
                    primary_id_list.append(PID)
    if p_id in DUP_ID_LIST:
        return True
    return False


def get_match_file_name():
    if OUTFILE:
        return OUTFILE
    now = datetime.now()
    return "Search_Results_Details_" + now.strftime("%d-%m-%Y_%H:%M:%S") + ".txt"


def get_path(primary_id):
    with open(ONSITE_LIST) as ol:
        reader = csv.reader(ol)
        for row in reader:
            if primary_id in row:
                for entry in row:
                    if "organised_data" in entry:
                        path_list = entry.split('/')
                        assay = path_list.pop(5)
                        path_list.append(assay)
                        path_list = ("/".join(path_list))
                        return path_list
                # This will work in future iterationsm with a better Onsite file:
                return str(os.path.split(row[-1])[0])
    return False


def get_location(scope, search_list, val_list, ref_list):
    # Creates an entry in a json format that displays the parameters of one search and all files matched to those params
    idx = 0
    pid_list = []

    results = {
        "parameters": [],
        "data": []
    }
    # Gather search parameters to specify which search this is displaying
    for query in search_list:
        param_string = str(query) + " = " + val_list[idx]
        results["parameters"].append(param_string)
        idx += 1

    # Get location of files
    for elem in scope["data"]:  # Cycle through all matches
        for inst in elem["instances"]:
            p_id = inst["primary_id"]
            ihec_path = get_path(p_id)
            if ihec_path: print(ihec_path)
            if path.exists(ihec_path) and os.path.isdir(ihec_path):
                print(ihec_path)
                for filename in os.listdir(ihec_path):  # Cycle through files in directory
                    if is_duplicate_pid(p_id, ref_list):
                        p_id = p_id + "_" + filename[0:8]
                        if p_id not in pid_list:
                            results["data"].append({
                                "ihec_id": elem["ihec_id"],
                                "experiment_type": inst["experiment_type"],
                                "primary_id": p_id,
                                "is live": elem["is live version?"],
                                "paths": [(str(ihec_path) + "/" + str(filename))],
                                "filename": [str(filename)]
                            })
                            pid_list.append(p_id)
                        else:
                            for res in results["data"]:
                                if p_id == res["primary_id"]:
                                    res["paths"].append((str(ihec_path) + "/" + str(filename)))
                                    res["filename"].append(str(filename))
    return results


def get_onsite_file(ref):
    dir = os.path.split(os.path.abspath(ref))[0]
    latest = date.min
    latest_file = ""
    for elem in os.listdir(dir):
        if "Onsite_Files_" in elem:
            date_str = elem.replace("Onsite_Files_", "")
            date_str = date_str[0:10]
            try:
                date_str = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (TypeError, ValueError) as e:
                date_str = None
            if date_str:
                if not latest_file:  #if date string exists, and latest file is empty
                    latest_file = elem
                    latest = date_str
                elif date_str > latest:
                    latest = date_str
                    latest_file = elem
    return os.path.abspath(latest_file)


args = parse_args()
check_args(args)
results = []
if args.outfile:
    OUTFILE = args.outfile

ONSITE_LIST = get_onsite_file(args.ref_table)

with open(args.query_table) as qt, open(args.ref_table, 'r') as rt:
    ref_table_json = json.load(rt)
    # get_location(ref_table_json["data"][10])
    query_table_csv = csv.reader(qt, delimiter='\t')
    search_list = get_search_list(query_table_csv)
    search_list_copy = copy.deepcopy(search_list)

    for row in query_table_csv:
        scope = copy.deepcopy(ref_table_json)  # reset scope for each search
        search_list = copy.deepcopy(search_list_copy)  # reset search list (values have been popped)
        query_list = []  # this will store the queries actually used in a given search
        val_list = []  # This will store the values to match for each query
        for val in row:
            try:
                search_param = search_list.pop(0)
            except IndexError:
                print("Column Missmatch. Please ensure all rows in the search "
                      "file have the same number of columns")
            val_to_match = val.casefold()
            if val_to_match:  # if string is not empty -> ie it is a valid search parameter
                query_list.append(search_param)
                val_list.append(val_to_match)
                scope = match_search_params(scope, search_param, val_to_match)
        results.append(get_location(scope, query_list, val_list, ref_table_json))

with open(get_match_file_name(), "w+") as outfile:
    json.dump(results, outfile, indent=4)
