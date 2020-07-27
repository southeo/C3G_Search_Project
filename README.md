# C3G_Search_Project
Compares user input to online EBI database and returns the location of the queried files. 

# Valid Search Parameters
Search parameters must be in the first line of the query file. Searches must include at least one of these parameters, copied exactly. 

Regular search Parameters:
- ihec_id
- project
- age_min
- age_max
- age_exact
- gender
- species
- markers
- biomaterial_provider


Instance Search Parameters:
- primary_id
- secondary_id
- assay_type
- experiment_type
- archive

Keyword Search parameters:
- donor_id
- tissue_keywords
- donor_ethnicity_keywords
- disease_keywords

# Regular Searches

# Instance Searches

# Keyword Searches

# Creating A Query File
A query file is one of two parameters passed into the search function. It contains all information you are searching for. The first line of the file contains all 

# Sample Input

project gender  assay_type  tissue_keywords
blueprint   chip-seq  cancer
  male  rna-seq 





# Updating Local Copy of EBI Database
