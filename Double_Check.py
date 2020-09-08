'''

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
    print(len(missed_loc), len(missed_files))


'''
import json
import csv

with open("EBI_Consolidated_test.txt") as rt:
    ref_table_json = json.load(rt)
    project_list = []
    markers_list = []
    biomat_list = []
    archive_list = []
    experiment_list = []
    assay_list = []
    count = 0
    for elem in ref_table_json ["data"]:
        if elem["project"] not in project_list:
            project_list.append(elem["project"])
        if "markers" in elem.keys() and elem["markers"] not in markers_list:
            markers_list.append(elem["markers"])
        if "biomaterial_provider" in elem.keys() and elem["biomaterial_provider"] not in biomat_list:
            biomat_list.append(elem["biomaterial_provider"])
        for inst in elem["instances"]:
            if inst["archive"] not in archive_list:
                archive_list.append(inst["archive"])
            if inst["experiment_type"] not in experiment_list:
                experiment_list.append(inst["experiment_type"].casefold())
            if inst["assay_type"] not in assay_list:
                assay_list.append(inst["assay_type"])
    assay_list = sorted(assay_list)
    experiment_list = sorted(experiment_list)
    project_list = sorted(project_list)

    for elem in experiment_list:
        print('\t', elem)
    print('\n')

'''
    for elem in archive_list:
        print(elem)
    print("\n")
    for elem in project_list:
        print('\t', elem)
    print("\n")
    '''


'''
    

    for elem in markers_list:
        print(elem)
    for elem in biomat_list:
        print('\t', elem)
    '''

'''

    print(count)


    #for elem in exp_list: print(elem)
       consolidate experiments, 
'''
'''


    print(len(dup_id_list), len(set(dup_id_list)), len(set(primary_id_list)))
    for elem in set(dup_id_list):
        print(elem)
''''''

with open("EBI_Database_Consolidated_2020-08-31.txt") as rt, open("On-Site_File_List_Sep2_2020.txt", "w") as sl:
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

'''