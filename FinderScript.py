import csv
import glob
import sys
import argparse
import os
import json
import copy

INSTANCE_SEARCHES = ["primary_id", "secondary_id", "assay_type", "experiment_type",
                     "archive"]  # these searches are handled differently
KEYWORD_SEARCHES = ["donor_keyword_id", "disease_keywords", "donor_ethnicity_keywords", "tissue_keywords"]
ID_PREFIXES = ["EGAR", "EGAF", "EGAD", "EGAX"]


def help():
    print("help info")


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
    return parser.parse_args()


def check_args(args):
    # make sure files exist
    assert (os.path.isfile(args.query_table)), "Query table not found"
    assert (os.path.isfile(args.ref_table)), "Reference table file not found"

    # first step: optional, update ref table from ebi website (keep old version)
    # Second step: search


def get_search_list(query_table):
    # reads query table and collects search functions
    search_list = []
    for elem in next(query_table_csv):
        search_list.append(elem.casefold())
    # print(search_list)
    return search_list


def match_search_params(scope, query, value, search_list):
    modified_scope = {"data": []}  # stores potential matches. This will limit the scope as searching progresses
    print(query, ", ", type(query))
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
                        bad_matches -= 1  # one less bad match
            if elem["instances"]:  # if instance list is not empty
                modified_scope["data"].append(elem)  # Append only the results with the correct instance searches
        elif query == "age_min" and query in elem.keys():
            print(value)
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
        else:
            if query in elem.keys() and value == str(elem[query]).casefold():
                modified_scope["data"].append(elem)
    return modified_scope


def print_results(scope, search_params, row):
    search_params_shortlist = []
    instance_flag = False
    # generate list of search parameters used in this particular query
    for elem in row:
        idx = row.index(elem)
        if elem:
            search_params_shortlist.append(search_params[idx])
    match_count = 0
    # print(search_params_shortlist, instance_flag)
    if scope["data"]:
        for elem in scope["data"]:
            print(elem)
            print("\n \n IHEC ID: ", elem["IHEC ID"])
            for param in search_params_shortlist:
                match_count += 1
                if param not in INSTANCE_SEARCHES:
                    print('\t', param, ":", elem[param], end="")
                else:
                    print("\n {  ", param, ": \n \t", end="")
                    for inst in elem["instances"]:
                        print(inst[param], ", ", end="")
                    print("\n }")
    print("\n Number of matches: ", match_count)


def fetch_id(filename):
    for prefix in ID_PREFIXES:
        idx = filename.find(prefix)
        if idx != -1:
            break
    return (filename[idx:idx + 15])


def get_location(scope):
    matches = {"data": []}
    path = "/genfs/projects/IHEC/soulaine_test/FinderProject/demo_search/" + scope["ihec_id"][0:14] + "/" + scope[
        "ihec_id"]
    print(path, " ", scope["ihec_id"])
    for inst in scope["instances"]:
        for filename in os.listdir(path):
            misc_id = fetch_id(str(filename))
            if misc_id == inst["primary_id"] or misc_id in inst["egar_id"] or misc_id in inst["egaf_id"]:
                matches["data"].append({
                    "ihec_id": scope["ihec_id"],
                    "path": path,
                    "ID" : misc_id
                })
    with open("Matches.txt", 'w') as outfile:
        json.dump(matches, outfile, indent=4)


with open("EBI_Consolidated_test") as rt:
    ref_table_json = json.load(rt)
    for elem in ref_table_json["data"]:
        if elem["ihec_id"] == "IHECRE00000309.2":
            idx = ref_table_json["data"].index(elem)
            break
    get_location(ref_table_json["data"][idx])
    # print(ref_table_json["data"][idx])
'''
args = parse_args()
check_args(args)
with open(args.query_table) as qt, open(args.ref_table) as rt:
    ref_table_json = json.load(rt)
    get_location(ref_table_json["data"][10])
    query_table_csv = csv.reader(qt, delimiter='\t')
    ref_table_json = json.load(rt)
    search_list = get_search_list(query_table_csv)
    search_list_copy = copy.deepcopy(search_list)


    for row in query_table_csv:
        scope = copy.deepcopy(ref_table_json)  # reset scope for each search
        search_list = copy.deepcopy(search_list_copy)  # reset search list (values have been popped)
        for val in row:
            try:
                search_param = search_list.pop(0)
            except IndexError:
                print("Column Missmatch. Please ensure all rows in the search "
                      "file have the same number of columns")
            val_to_match = val.casefold()
            if search_param == "donor_age" or search_param == "age_min" or search_param == "age_max":
                val_to_match = val_to_match.split(",")  # take age as a list with 3 properties: val, unit, flag
            print(val_to_match)
            if val_to_match:  # if string is not empty -> ie it is a valid search parameter
                scope = match_search_params(scope, search_param, val_to_match, search_list_copy)
        print_results(scope, search_list_copy, row)


'''
