import csv
import glob
import sys
import argparse
import os
from os import path
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
                        bad_matches -= 1  # one less bad match
            if elem["instances"]:  # if instance list is not empty
                modified_scope["data"].append(elem)  # Append only the results with the correct instance searches
                # print("Matches so far: ",len(scope),"\t Elem[Query: ", inst[query], "\t Query: ", query)
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
                # print("Matches so far: ",len(scope),"\t Elem[Query: ", elem[query], "\t Query: ", query)
        else:
            if query in elem.keys() and value == str(elem[query]).casefold():
                modified_scope["data"].append(elem)
    # print("Matches so far: ", len(modified_scope["data"]))
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
            print("\n \n IHEC ID: ", elem["ihec_id"])
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


def get_location(scope, search_list, val_list):
    results = {
        "parameters": [],
        "data": []
    }
    idx = 0

    for query in search_list:
        if query in INSTANCE_SEARCHES:
            param_string = str(query) + " = " + val_list[idx]
        else:
            param_string = str(query) + " = " + val_list[idx]
        results["parameters"].append(param_string)
        idx += 1

    for elem in scope["data"]:  # Cycle through all matches
        ihec_path = "/genfs/projects/IHEC/soulaine_test/FinderProject/demo_search/" + elem["ihec_id"][0:14] + "/" + \
                    elem["ihec_id"]  # get path to where the file SHOULD be...
        if path.exists(ihec_path):
            for inst in elem["instances"]:  # Cycle through instances of each match
                for filename in os.listdir(ihec_path):  # Cycle through files in directory
                    misc_id = fetch_id(str(filename))  # Matches filename to instance
                    
                    if misc_id == inst["primary_id"] or misc_id in inst["egar_id"] or misc_id in inst["egaf_id"]:
                        if "read1" in str(filename):
                            for res in results["data"]:
                                print("Res id: ", res["ihec_id"], "elem id: ", elem["ihec_id"])
                                if res["ihec_id"] == elem["ihec_id"]:
                                    res["read_1_path"] = (str(ihec_path) + "/" + str(filename))
                            if "read_1_path" not in elem.keys():
                                results["data"].append({
                                    "ihec_id": elem["ihec_id"],
                                    "read_1_path": (str(ihec_path) + "/" + str(filename)),
                                })
                        elif "read2" in str(filename):
                            for res in results["data"]:
                                print("Res id: ", res["ihec_id"], "elem id: ", elem["ihec_id"])
                                if res["ihec_id"] == elem["ihec_id"]:
                                    res["read_2_path"] = (str(ihec_path) + "/" + str(filename))
                            if "read_1_path" not in elem.keys():
                                results["data"].append({
                                    "ihec_id": elem["ihec_id"],
                                    "read_1_path": (str(ihec_path) + "/" + str(filename)),
                                })

                        else:
                            results["data"].append({
                                "ihec_id": elem["ihec_id"],
                                "path": (str(ihec_path) + "/" + str(filename)),
                            })
                        '''for param in search_list:
                            if param in INSTANCE_SEARCHES:
                                results["data"][-1][param] = inst[param]
                            else:
                                results["data"][-1][param] = elem[param]'''
    return results
    '''
    with open("Matches.txt", 'w') as outfile:
        json.dump(results, outfile, indent=4)
    '''


args = parse_args()
check_args(args)
results = []
with open(args.query_table) as qt, open(args.ref_table) as rt:
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
                results.append(get_location(scope, query_list, val_list))

with open("Matches.txt", "w") as outfile:
    json.dump(results, outfile, indent=4)
