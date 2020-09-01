import json

with open("EBI_Database_Consolidated_2020-08-31.txt", 'r') as rt, open("Matches.txt") as mt:
    ref_table_json = json.load(rt)
    matches = json.load(mt)
    matches = matches[1]
    file_list = []
    good_files = []
    missed_files = []
    for elem in matches:
        for data in matches["data"]:
            file_list.append(data["filename"])


    for elem in ref_table_json["data"]:
        for inst in elem["instances"]:
            if (inst['assay_type']).casefold() == ("RNA-Seq").casefold() and "filename" in inst.keys():
                for file in inst["filename"]:
                    if file in file_list:
                        good_files.append(file)
                    else:
                        missed_files.append(file)

    print("Search Results: ", len(file_list), ", Good Matches: ", len(good_files), ", Missed files:", len(missed_files))




