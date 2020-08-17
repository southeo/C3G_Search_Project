#!/bin/sh
#SBATCH --time=10:00:00
#SBATCH --account=def-bourqueg
chmod +x Move_List.txt 
python data_organization.py -r $PWD -d ../../ihec_data_struct/ -s ../../../jbodpool_mp2/
