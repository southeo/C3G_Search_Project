import shutil
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from bs4 import BeautifulSoup
from shutil import copyfile
import os
from datetime import date
import math
import datetime

IHEC_PORTAL_URL = "https://www.ebi.ac.uk/vg/epirr/view/"  # must be cat'd with "all" or IHECRE ID
remove_char_list = [',', '.', ';', '(', ')', '-', '/', '_', '\'', '\"']
RAW_FILE = "EBI_Database_Raw.txt_2020-08-26.txt"     #"EBI_Database_Raw.txt_" + str(date.today()) + ".txt"

def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None, ):
    """Retry timeout requests"""
    session = session or requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist, )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def parse_ihec_page(url):
    # Parses single web page based on url (which includes IHEC_RE ID)

    metadata_dict = dict()

    ihec_response = requests_retry_session().get(url)
    if ihec_response.ok:
        soup = BeautifulSoup(ihec_response.content, 'html.parser')  # object that parses html

        # Metadata: This will be the same for each item associated with a given IHEC ID. Create single dictionary
        # each entry can pull from
        ihec_id = soup.find("h1")  # IHEC ID
        dd_list = soup.find_all("dd")  # Metadata that applies to all files associated with this IHEC ID
        dt_list = soup.find_all("dt")  # Metadata specific to each file (e.g. assay type)

        count = 0
        metadata_dict['ihec_id'] = ihec_id.string
        while count < len(dd_list):
            metadata_dict[str(dt_list[count].string).casefold()] = str(dd_list[count].string).casefold()
            count += 1
        metadata_dict['instances'] = []  # this will be filled in in next step

        # Instance Data: This will be different for each item. Create dictionary that will be unique for each entry.
        # Not that metadata changes from one IHEC ID to another, but this data has the same format
        table = soup.find('table')
        table_rows = table.find_all('tr')
        for tr in table_rows:
            td = tr.find_all('td')
            if len(td) != 0:  # make sure there is data
                metadata_dict['instances'].append({
                    "primary_id": td[3].string,
                    "secondary_id": td[4].string,
                    "assay_type": td[0].string,
                    "experiment_type": td[1].string,
                    "archive": td[2].string,
                })
        return metadata_dict


def parse_ihec_db():  # parses entire EBI database
    ihec_response = requests_retry_session().get(IHEC_PORTAL_URL + "all")  # Get connected
    if ihec_response.ok:
        soup = BeautifulSoup(ihec_response.content, 'html.parser')
        ebi_dict = {'data': []}
        id_list = []
        # Put all ihec ids in a list. This will allow the program to navigate the web portal
        for row in soup.find_all('table')[0].tbody.find_all('tr'):
            id_list.append(row.find_all('td')[3].contents)
        # Parse each page in the web portal
        for ihec_id in id_list:
            ebi_dict['data'].append(parse_ihec_page(IHEC_PORTAL_URL + ihec_id[0]))
            print(ihec_id[0], " Complete")

        # write raw results
        with open(RAW_FILE, 'w') as outfile:
            json.dump(ebi_dict, outfile, indent=4)


def consolidate_tissue(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)
        for elem in db_json["data"]:
            tissue_keywords = []
            if "tissue_type" in elem and elem["tissue_type"] is not None:
                tissue_keywords.append(elem["tissue_type"])
            if "tissue-type" in elem and elem["tissue-type"] is not None:
                tissue_keywords.append(elem["tissue-type"])
            if "tissue" in elem and elem["tissue"] is not None:
                tissue_keywords.append(elem["tissue"])
            if "origin_sample" in elem and elem["origin_sample"] is not None:
                tissue_keywords.append(elem["origin_sample"])
            if "cell ontology" in elem and elem["cell ontology"] is not None:
                tissue_keywords.append(elem["cell ontology"])
            if "lineage" in elem and elem["lineage"] is not None:
                tissue_keywords.append(elem["lineage"])
            if "cell_type" in elem and elem["cell_type"] is not None:
                tissue_keywords.append(elem["cell_type"])
            if "histological_type" in elem and elem["histological_type"] is not None:
                tissue_keywords.append(elem["histological_type"])

            elem["tissue_keywords"] = remove_bad_chars(tissue_keywords)

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_gender(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)
        for elem in db_json["data"]:
            if "gender" not in elem:
                if "donor_sex" in elem and elem["donor_sex"] is not None:
                    elem["gender"] = elem["donor_sex"]
                elif "sex" in elem and elem["sex"] is not None:
                    elem["gender"] = elem["sex"]

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_ethnicity(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)
        for elem in db_json['data']:
            ethnicity_keywords = []
            if "population" in elem and elem["population"] is not None:
                ethnicity_keywords += elem["population"].split()
            if "ethnicity" in elem and elem["ethnicity"] is not None:
                ethnicity_keywords += elem["ethnicity"].split()
            if "donor_ethnicity" in elem and elem["donor_ethnicity"] is not None:
                ethnicity_keywords += elem['donor_ethnicity'].split()

            # make searching a little easier:
            if "white" in ethnicity_keywords or "White" in ethnicity_keywords:
                ethnicity_keywords.append("caucasian")
            elif "Caucasian" in ethnicity_keywords or "caucasian" in ethnicity_keywords:
                ethnicity_keywords.append("white")
            if "african" in ethnicity_keywords and "american" in ethnicity_keywords or "aa" in ethnicity_keywords:
                ethnicity_keywords.extend(["black", "african american"])
            if "native" in ethnicity_keywords and "american" in ethnicity_keywords:
                ethnicity_keywords.extend(["first", "nations", "indigenous"])
            if ethnicity_keywords:
                elem['donor_ethnicity_keywords'] = remove_bad_chars(ethnicity_keywords)

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_donor_id(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)
        for elem in db_json["data"]:
            id_keywords = []
            if "donor id" in elem and elem["donor id"] is not None:
                id_keywords.append(elem["donor id"])
            if "subject_id" in elem and elem["subject_id"] is not None:
                id_keywords.append(elem["subject_id"])
            if "sample_id" in elem and elem["sample_id"] is not None:
                id_keywords.append(elem["sample_id"])
            if "donor_id" in elem and elem["donor_id"] is not None:
                id_keywords.append(elem["donor_id"])
            elem["donor_keyword_id"] = id_keywords

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_local_id(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)
        for elem in db_json["data"]:
            for inst in elem["instances"]:
                local_ids = []
                if "primary_id" in inst and inst["primary_id"] is not None:
                    local_ids.append(inst["primary_id"])
                if "secondary_id" in inst and inst["secondary_id"] is not None:
                    local_ids.append(inst["secondary_id"])
                if "egaf_id" in inst and inst["egaf_id"] is not None:
                    for egaf in inst["egaf_id"]:
                        local_ids.append(egaf)
                if "egar_id" in inst and inst["egar_id"] is not None:
                    for egar in inst["egar_id"]:
                        local_ids.append(egar)
                inst["local_ids"] = local_ids
    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def is_float(str):
    try:
        float(str)
        return True
    except ValueError:
        return False


def age_in_years(age_list, divisor):
    new_age_list = []
    for val in age_list:
        new_age_list.append((math.trunc(val * 100 / divisor) / 100))
    return new_age_list


def consolidate_age(data_file):
    with open(data_file, "r") as database_file:
        db_json = json.load(database_file)

        for elem in db_json["data"]:
            if "age" in elem.keys():
                char_list = elem["age"].split()
            elif "donor_age" in elem.keys():
                char_list = elem["donor_age"].split()
            else:
                char_list = []
            if char_list:
                float_list = []
                while len(char_list) != 0:
                    next_char = char_list.pop()  # clear out the characters, keep the numbers
                    if is_float(next_char):
                        float_list.append(float(next_char))
                if float_list:
                    if "donor_age_unit" in elem.keys():
                        if elem["donor_age_unit"] == "day":
                            float_list = age_in_years(float_list, 365)
                        elif elem["donor_age_unit"] == "week":
                            float_list = age_in_years(float_list, 52)
                        elif elem["donor_age_unit"] == "month":
                            float_list = age_in_years(float_list, 12)
                    elem["age_min"] = min(float_list)  # First element in the age list will be value
                    elem["age_max"] = max(float_list)
                    if elem["age_min"] == elem["age_max"]:
                        elem["age_exact"] = elem["age_min"]
                    else:
                        elem["age_exact"] = ("")  # if there is a range this key does not contain useful info
            if "donor_life_stage" in elem.keys() and \
                    (elem["donor_life_stage"] == "fetal" or elem["donor_life_stage"] == "embryonic"):
                elem["prenatal"] = True
            else:
                elem["prenatal"] = False

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_disease(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)

        for elem in db_json["data"]:
            disease_list = []
            if "disease" in elem and elem["disease"] is not None:
                disease_list.append(elem["disease"])
            if "donor_health_status" in elem and elem["donor_health_status"] is not None:
                disease_list.append(elem["donor_health_status"])
            elem["disease_keywords"] = remove_bad_chars(disease_list)

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_experiment(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)

        for elem in db_json["data"]:
            for inst in elem["instances"]:
                exp = inst["experiment_type"]
                if exp == "RNA": exp = "RNA-Seq"
                elif exp == "H3K4me3":  exp = "Histone H3K4me3"
                elif exp == "H3K27ac": exp = "Histone H3K27ac"

                if "Histone" in exp: exp = "ChIP-Seq " + exp

                db_json["experiment_type"] = exp.casefold()

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_all(data_file):
    consolidated_file = "EBI_Database_Consolidated_" + str(date.today()) + ".txt"
    egad_map = "egad_file_mapping.json"

    if not os.path.isfile(consolidated_file):
        copyfile(data_file, consolidated_file)  # Make copy of this file with new name
    else:
        consolidated_file = consolidated_file + "_" + (datetime.datetime.now()).strftime("%H:%M:%S")
        copyfile(data_file, consolidated_file)

    # consolidate and clean data
    consolidate_age(consolidated_file)
    consolidate_disease(consolidated_file)
    consolidate_donor_id(consolidated_file)
    consolidate_ethnicity(consolidated_file)
    consolidate_gender(consolidated_file)
    consolidate_tissue(consolidated_file)
    consolidate_experiment(consolidated_file)
    link_ega_ids(egad_map, consolidated_file)
    consolidate_local_id(consolidated_file)


def link_ega_ids(egad_map, consolidated_file):  # Links EGA IDs (EGAF, EGAX, EGAR, EGAD) to IHEC id
    with open(os.path.abspath(egad_map)) as egad_mtd, open(consolidated_file, "r") as ebi_db:
        egad_json = json.load(egad_mtd)
        ebi_json = json.load(ebi_db)
        for egad in egad_json:
            for elem in ebi_json["data"]:
                for inst in elem["instances"]:
                    if egad == inst["secondary_id"]:
                        for egax in egad_json[egad]:
                            if egax == inst["primary_id"]:
                                inst["egar_id"] = []
                                inst["egaf_id"] = []
                                for egar in egad_json[egad][egax]:
                                    inst["egar_id"].append(egar)
                                    for egaf in egad_json[egad][egax][egar]:
                                        inst["egaf_id"].append(egaf)
    with open(consolidated_file, "w") as ebi_db:
        json.dump(ebi_json, ebi_db, indent=4)


def remove_bad_chars(keywords):
    new_list = []
    for kw in keywords:
        for char in remove_char_list:
            kw = kw.replace(char, " ")
        new_list.extend(kw.split())
    return list(set(new_list))


def match_files(consolidated_file):
    pass



def get_keyword_list(ebi_db):
    with open(ebi_db) as ebi_db:
        ebi_json = json.load(ebi_db)
        disease_keywords = []
        tissue_keywords = []
        ethnicity_keywords = []
        for elem in ebi_json["data"]:
            if elem["disease_keywords"]:
                for key1 in elem["disease_keywords"]:
                    if key1 not in disease_keywords:
                        disease_keywords.append(key1)
            if elem["tissue_keywords"]:
                for key2 in elem["tissue_keywords"]:
                    if key2 not in tissue_keywords:
                        tissue_keywords.append(key2)
            if elem["donor_ethnicity_keywords"]:
                for key3 in elem["donor_ethnicity_keywords"]:
                    if key3 not in ethnicity_keywords:
                        ethnicity_keywords.append(key3)

        disease_keywords = sorted(disease_keywords)
        tissue_keywords = sorted(tissue_keywords)
        ethnicity_keywords = sorted(ethnicity_keywords)


#parse_ihec_db()
consolidate_all("EBI_Database_Consolidated_2020-08-31.txt")
