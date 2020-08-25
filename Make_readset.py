import csv
import json
import argparse
import os
from datetime import date

HEADING = ['Sample', 'Readset', 'Library', 'RunType', 'Run', 'Lane', 'Adapter1', 'Adapter2', 'QualityOffset', 'BED',
           'FASTQ1', 'FASTQ2', 'BAM']

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r',
                        '--results_table',
                        help="Results of search",
                        required=True)
    return parser.parse_args()


def check_args(args):
    # make sure directories exist
    assert (os.path.isdir(args.results_table)), "Source directory not found"




args = parse_args()
check_args(args)

with open(args.results_table, 'r') as rt, open(str("Readset_"+str(date.today())+".txt"), "w") as outfile:
    search_results = json.load(rt)
    for elem in search_results:
        pass



