# C3G_Search_Project
Compares user input to online EBI database and returns the location of the queried files. 

## Valid Search Parameters
Search parameters must be in the first line of the query file. Searches must include at least one of these parameters, copied exactly. 

### Regular search Parameters
Regular searches match the string in the query file to the metadata associated with each IHEC ID. All associated instances will be flagged as matches. 

- ihec_id (Note: a different version will not be considered a match)
- project
- age_min
- age_max
- age_exact
- gender
- species
- markers
- biomaterial_provider


### Instance Search Parameters:
Each IHEC ID corresponds to a number of instances, or datasets. These datasets may have differing associated IDs, assay_types, etc. 

- primary_id
- secondary_id
- assay_type
- experiment_type
- archive

### Keyword Search parameters:
All items in input must be satisfied, but there may be extra keywords in the search element. For instance, a dataset may have "cord blood" listed as its tissue type. A keyword search using either "cord", "blood", or both will yield a match. However, if the dataset only has "blood" as its tissue type, a search for "cord blood" will not result in a match. 

- donor_id (stored as donor id, donor_id, or sample_id on the EBI Database)
- tissue_keywords
- donor_ethnicity_keywords
- disease_keywords

## Creating A Query File
A query file is one of two parameters passed into the search function. It contains all information you are searching for. The first line of the file contains all 

## Sample Input

project gender  assay_type  tissue_keywords
blueprint   chip-seq  cancer
  male  rna-seq 





# Updating Local Copy of EBI Database
