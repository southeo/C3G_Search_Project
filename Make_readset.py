import csv
import json
import argparse
import os
from datetime import date

HEADING = ['Sample', 'Readset', 'Library', 'RunType', 'Run', 'Lane', 'Adapter1', 'Adapter2', 'QualityOffset', 'BED',
           'FASTQ1', 'FASTQ2', 'BAM']
REF_TABLE = "EBI_Consolidated_test.txt"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s',
                        '--search_results',
                        help="Results of search done with FinderScript.py",
                        required=True)
    parser.add_argument('-r',
                        '--reference_table',
                        help="Master metadata file pulled from EBI Web Portal",
                        required=True)
    return parser.parse_args()


def check_args(args):
    # make sure directories exist
    assert (os.path.isdir(args.search_results)), "Search results not found"
    assert (os.path.isdir(args.search_results)), "Metadata file not found"


def get_misc_id(ihec_id):
    pass

args = parse_args()
check_args(args)

with open(args.results_table, 'r') as sr, \
        open(args.reference_table, 'r') as rt, \
        open(str("Readset_"+str(date.today())+".txt"), "w") as outfile:

    search_results = json.load(sr)
    ref_table = json.load(rt)
    writer = csv.writer(outfile)

    for elem in search_results:
        row = []
        for results in elem["data"]:


            # determine read type
            if "r1_path" in results.keys() and "r2_path" in results.keys():
                pass



