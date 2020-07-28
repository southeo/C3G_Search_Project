#!/bin/sh
#SBATCH --time=10:00:00
#SBATCH --account=def-bourqueg
chmod +x not_downloaded.txt
python data_organization.py>not_downloaded.txt
