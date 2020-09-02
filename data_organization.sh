#!/bin/sh
#SBATCH --time=18:00:00
#SBATCH --account=def-bourqueg
chmod +x Move_List_2.txt
chmod +x Duplicate_list.txt
python data_organization.py -d ../../Epigenomic_Data_Home/ -s ../../../jbodpool_mp2/EpiVar/EGAD00001002675 -r $PWD -m True
