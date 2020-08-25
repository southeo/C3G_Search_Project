import os
from datetime import datetime
from datetime import date

def get_ref_table(ref_dir):
    latest = date.min
    print(latest)
    for elem in os.listdir(ref_dir):
        if "EBI_Database_Consolidated_" in elem:
            date_str = elem.replace("EBI_Database_Consolidated_", "")
            date_str = date_str.replace(".txt", "")
            date_str = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date_str > latest:
                latest = date_str
                latest_file = elem
    return latest_file


print(get_ref_table(os.getcwd()))
