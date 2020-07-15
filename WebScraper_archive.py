# General import
import shutil
from urllib.request import urlopen
from collections import defaultdict
from multiprocessing import Pool, Manager
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from lxml import html
from bs4 import BeautifulSoup
import pandas as pd
import re
from shutil import copyfile
import os
from datetime import date

IHEC_PORTAL_URL = "https://www.ebi.ac.uk/vg/epirr/view/"  # must be cat'd with "all" or IHECRE ID
remove_char_list = [',', '.', ';', '(', ')']


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
    rawdata_dict = dict()

    ihec_response = requests_retry_session().get(url)
    if ihec_response.ok:
        soup = BeautifulSoup(ihec_response.content, 'html.parser')  # object that parses html

        # Metadata: This will be the same for each item associated with a given IHEC ID. Create single dictionary
        # each entry can pull from
        ihec_id = soup.find("h1")  # IHEC ID
        dd_list = soup.find_all("dd")  #
        dt_list = soup.find_all("dt")

        count = 0
        metadata_dict['ihec_id'] = ihec_id.string
        while count < len(dd_list):
            metadata_dict[str(dt_list[count].string).casefold()] = str(dd_list[count].string).casefold()
            count += 1
        metadata_dict['instances'] = []  # this will be filled in in next step

        # Raw Data: This will be different for each item. Create dictionary that will be unique for each entry.
        # Not that metadata changes from one IHEC ID to another, but this data has the same format
        table = soup.find('table')
        table_rows = table.find_all('tr')
        for tr in table_rows:
            rawdata_dict = ()  # reset vals -> necessary in python?
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


def parse_ihec_db():
    # parses entire EBI database
    ihec_response = requests_retry_session().get(IHEC_PORTAL_URL + "all")
    if ihec_response.ok:
        soup = BeautifulSoup(ihec_response.content, 'html.parser')
        ebi_dict = {'data': []}
        id_list = []
        # put all ihec ids in a list:
        for row in soup.find_all('table')[0].tbody.find_all('tr'):
            id_list.append(row.find_all('td')[3].contents)
        for ihec_id in id_list:
            ebi_dict['data'].append(parse_ihec_page(IHEC_PORTAL_URL + ihec_id[0]))
            print(ihec_id[0], " Complete")

        # write raw results
        with open('EBI_Database_Raw.txt', 'w') as outfile:
            json.dump(ebi_dict, outfile, indent=4)



def consolidate_tissue(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)
        for elem in db_json["data"]:
            tissue_keywords = []
            if "tissue_type" in elem and elem["tissue_type"] is not None:
                tissue_keywords += elem["tissue_type"].split()
            if "tissue-type" in elem and elem["tissue-type"] is not None:
                tissue_keywords += elem["tissue-type"].split()
            if "tissue" in elem and elem["tissue"] is not None:
                tissue_keywords += elem["tissue"].split()
            if "origin_sample" in elem and elem["origin_sample"] is not None:
                tissue_keywords += elem["origin_sample"].split()
            if "cell ontology" in elem and elem["cell ontology"] is not None:
                tissue_keywords += elem["cell ontology"].split()
            if "lineage" in elem and elem["lineage"] is not None:
                tissue_keywords += elem["lineage"].split()
            if "cell_type" in elem and elem["cell_type"] is not None:
                tissue_keywords += elem["cell_type"].split()
            if "histological_type" in elem and elem["histological_type"] is not None:
                tissue_keywords += elem["histological_type"].split()

            elem["tissue_keywords"] = tissue_keywords

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
                ethnicity_keywords.append("Caucasian")
            elif "Caucasian" in ethnicity_keywords:
                ethnicity_keywords.append("White")
            if "African" in ethnicity_keywords and "American" in ethnicity_keywords or "AA" in ethnicity_keywords:
                ethnicity_keywords.extend(["Black", "African American"])
            if "Native" in ethnicity_keywords and "American" in ethnicity_keywords:
                ethnicity_keywords.extend(["Native American", "First Nations", "Indigenous"])
            elem['donor_ethnicity_keywords'] = ethnicity_keywords

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_age(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)
        for elem in db_json['data']:
            if "donor_age" not in elem:
                if "age" in elem and elem['age'] is not None:
                    elem["donor_age"] = elem["age"]
            if "donor_life_stage" in elem and elem["donor_life_stage"] is not None:
                if elem["donor_life_stage"] == "embryonic" or elem["donor_life_stage"] == "fetal":
                    elem["prenatal"] = True
                else:
                    elem["prenatal"] = False
            else:
                elem["prenatal"] = False

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


def consolidate_disease(data_file):
    with open(data_file, 'r') as database_file:
        db_json = json.load(database_file)

        for elem in db_json["data"]:
            disease_list = []
            if "disease" in elem and elem["disease"] is not None:
                # remove some formatting issues
                elem["disease"] = elem["disease"].replace(",", "")
                elem["disease"] = elem["disease"].replace(";", "")
                elem["disease"] = elem["disease"].replace("(", "")
                elem["disease"] = elem["disease"].replace(")", "")
                elem["disease"] = elem["disease"].replace("_", " ")
                # add each term to keywords list
                disease_list = elem["disease"].split()
            if "donor_health_status" in elem and elem["donor_health_status"] is not None:
                disease_list += elem["donor_health_status"].split()

            elem["disease_keywords"] = disease_list

    with open(data_file, 'w') as outfile:
        json.dump(db_json, outfile, indent=4)


def consolidate_all(data_file):
    home_dir = os.getcwd() + '\\' + data_file
    raw_dir = os.getcwd() + '\Raw_DB\EBI_Database_' + str(date.today()) + ".txt"
    consolidated_file = "EBI_Database_Consolidated_" + str(date.today()) + ".txt"
    if not os.path.isfile(consolidated_file):
        shutil.copy2(home_dir, raw_dir)
        os.rename(data_file, consolidated_file)
        # consolidate data
        consolidate_age(consolidated_file)
        consolidate_disease(consolidated_file)
        consolidate_donor_id(consolidated_file)
        consolidate_ethnicity(consolidated_file)
        consolidate_gender(consolidated_file)
        consolidate_tissue(consolidated_file)



#parse_ihec_db()
consolidate_all("EBI_Database_Raw.txt")


