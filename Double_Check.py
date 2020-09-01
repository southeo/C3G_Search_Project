import json

with open("EBI_Database_Consolidated_2020-08-31.txt", 'r') as rt, open("Matches.txt") as mt:
    ref_table_json = json.load(rt)
    matches = json.load(mt)
    matches = matches[1]
    file_list = []
    good_files = []
    missed_files = []
    missed_loc = []
    for elem in matches:
        for data in matches["data"]:
            file_list.append(data["filename"])


    for elem in ref_table_json["data"]:
        for inst in elem["instances"]:
            if (inst['assay_type']).casefold() == ("RNA-Seq").casefold() and "filename" in inst.keys():
                for tuple in inst["filename"]:
                    file= tuple[0]
                    if file in file_list:
                        good_files.append(file)
                    else:
                        missed_files.append(file)
                        missed_loc.append(elem["ihec_id"])
    missed_files = set(missed_files)
    missed_loc = set(missed_loc)
#    print("Search Results: ", len(set(file_list)), ", Good Matches: ", len(set(good_files)), ", Missed files:", len(set(missed_files)))


    for missed in missed_loc:
        print(missed)
    print(len(missed_loc))



