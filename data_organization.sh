#!/bin/sh
#SBATCH --time=18:00:00
#SBATCH --account=def-bourqueg
chmod +x Move_List_with_egaf.txt
chmod +x Duplicate_list_all.txt
python data_organization.py -r $PWD -d ../../ihec_data_struct/ -s ../../../jbodpool_mp2/
