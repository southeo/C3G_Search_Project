import csv
#import json
import argparse
import os
from datetime import date
import simplejson as json

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
    assert (os.path.isfile(args.search_results)), "Search results not found"
    assert (os.path.isfile(args.reference_table)), "Metadata file not found"


def get_misc_id(ihec_id, filename, ref_table):
    for elem in ref_table["data"]:
        if elem["ihec_id"] == ihec_id:
            for inst in elem["instances"]:
                for fn in inst["filename"]:
                    if fn[0] == filename:
                        return fn[1]


def get_run(ihec_id, this_run_count, sample_run_mapping):
    if not sample_run_mapping:
        sample_run_mapping = [(ihec_id, this_run_count)]

    else:
        in_table = False
        for tup in sample_run_mapping:
            if tup[0] == ihec_id:
                in_table = True
                this_run_count = tup[1]
        if not in_table:
            sample_run_mapping.append((ihec_id, this_run_count))
    return this_run_count, sample_run_mapping


def get_paths(results):
    if "path" in results.keys():
        path1 = results["path"]
        path2 = None
    elif "r2_path" in results.keys():
        path1 = results["r1_path"]
        path2 = results["r2_path"]
    elif "r1_path" in results.keys():
        path1 = results["r1_path"]
        path2 = None
    return path1, path2


args = parse_args()
check_args(args)

with open(args.search_results, 'r') as sr, open(args.reference_table, 'r') as rt:
    search_results = json.load(sr)
    ref_table = json.load(rt)

    search_count = 0
    lane_count = 0

    for elem in search_results:
        search_count += 1
        readset_file = "Readset_" + str(date.today()) + "_Search_" + str(search_count) + ".txt"
        lane_count += 1
        sample_run_mapping = []
        # Produce a new readset file per search result

        with open(readset_file, 'w') as outfile:
            writer = csv.writer(outfile, delimeter='\t')
            writer.writerow(HEADING)
            row = []
            this_run_count = 0
            for results in elem["data"]:
                fastq1 = '\t'
                fastq2 = '\t'
                bam = '\t'
                path1, path2 = get_paths(results)
                if "bam" in path1 or "fastq" in path1:  #if file is correct type
                    this_run_count += 100
                    sample = results["ihec_id"]
                    filename = path1.split('/')[-1]
                    readset = get_misc_id(sample, filename, ref_table)
                    if path2:
                        print(path2)
                        run_type = "PAIRED_END"
                        fastq1 = path1
                        fastq2 = path2
                    else:
                        run_type = "SINGLE_END"
                        if "fastq" in path1:
                            fastq1 = path1
                        else:
                            bam = path1

                    run = "run" + str(this_run_count)
                    this_run_count, sample_run_mapping = get_run(sample, this_run_count, sample_run_mapping)
                    # TODO: figure out best way to take in user input for adapters. One for all search results? One for each search?
                    adapter1 = "AGATCGGAAGAGCACACGTCTGAACTCCAGTCA"
                    adapter2 = "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT"
                    row = [sample, readset, '\t', run_type, this_run_count, lane_count,
                           adapter1, adapter2, '\t', '\t', fastq1, fastq1, bam]
                    writer.writerow(row)








