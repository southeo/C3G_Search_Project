#!/bin/sh
#SBATCH --time=96:00:00
#SBATCH --account=def-bourqueg
chmod +x Duplicate_list_all.txt
chmod +x False_dups.txt
python Duplicate_Checker.py
