import argparse

from bigquery import get_client

from gh_api import get_language_bytes
from local_params import json_key_final_dataset
from util import curr_time_utc
from util import delete_bq_table, create_bq_table, push_bq_records
from util import get_repo_names
from util import curr_commit_master


parser = argparse.ArgumentParser()
parser.add_argument('--ds', action = 'store', dest = 'ds', required = True, 
                    help = 'BigQuery dataset to write table to')
parser.add_argument('--table', action = 'store', dest = 'table', required = True, 
                    help = 'BigQuery table to write to')
parser.add_argument('--sheet', action = 'store', dest = 'sheet', required = True, 
                    help = 'Google Sheet with use_repo as a column')
args = parser.parse_args()
 
dataset = args.ds
table = args.table
sheet = args.sheet
 
# Get repo names
print("Getting repo names from spreadsheet")
repos = get_repo_names(sheet)
print("There are %s repos with use_repo = 1.\n" % len(repos))

# Using BigQuery-Python https://github.com/tylertreat/BigQuery-Python
print('\nGetting BigQuery client\n')
client = get_client(json_key_file=json_key_final_dataset, readonly=False, swallow_results=True)
 
# Delete the output table if it exists
delete_bq_table(client, dataset, table)
 
# Create the output table
schema = [
    {'name': 'repo_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language_name', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'language_bytes', 'type': 'INTEGER', 'mode': 'NULLABLE'},
    {'name': 'curr_commit_master', 'type': 'STRING', 'mode': 'NULLABLE'},
    {'name': 'time_accessed', 'type': 'STRING', 'mode': 'NULLABLE'}
]
create_bq_table(client, dataset, table, schema)

# Get list of language records for a repo
def get_records(repo_name):
    data = get_language_bytes(repo_name)
    curr_time = curr_time_utc()
    curr_commit = curr_commit_master(repo_name)
    return [{'repo_name': repo_name, 
             'language_name': key, 
             'language_bytes': data[key],
             'curr_commit_master': curr_commit,
             'time_accessed': curr_time} for key in data.keys()]
    
print("Getting language info from GitHub API")
records = []
num_done = 0
for repo_name in repos:
    try:
        for record in get_records(repo_name):
            records.append(record)
    except UnicodeEncodeError:
        print("Skipping repo %s" % repo_name)
    num_done = num_done + 1
    if num_done % 100 == 0:
        print("Finished %s repos. Pushing records." % num_done)
        push_bq_records(client, dataset, table, records)
        records.clear()
push_bq_records(client, dataset, table, records) # Last batch




