#!/usr/bin/env python
# coding: utf-8

# # Imports

# from airtable_config import *
import pathlib
import json
import os
import sys
from datetime import datetime

from pyairtable import metadata
from pyairtable import Base
from pyairtable import Table, retry_strategy
import time
import logging
import tarfile
import lzma


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')


from upload_download_functions import *





# # logging

console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file


# # Constants

api_key = os.environ['AIRTABLE_API_KEY']
base_id = os.environ['BASE_ID']


my_retry_strategy = retry_strategy(total=3, backoff_factor=2)


# # Functions

def get_table(table_id, retry_strategy=my_retry_strategy):
    table = Table(api_key, base_id, table_id, retry_strategy=retry_strategy)
    return table


def get_base_schema():
    base = Base(api_key,base_id)
    schema = metadata.get_base_schema(base)
    return(schema)


# # Backup schema

def compress_folder_to_tar_xz(folder_path, output_file):
    with lzma.open(output_file, "w") as f:
        with tarfile.open(fileobj=f, mode="w") as tar:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    tar.add(file_path, arcname=os.path.relpath(file_path, folder_path))


while True:
    # prepare folder
    now = str(datetime.now())
    
    backup_folder = pathlib.Path( f"../airtable_backups/airtable_{now}")
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        
    
    # backup schema
    schema=get_base_schema()
    
    with open(backup_folder/"schema.json","w") as json_file:
        json.dump(schema, json_file, indent=4)
    
    # backup tables
    for table in schema.get("tables"):
        
        table_id = table.get("id")
        table = get_table(table_id)
        
        data = table.all()
        with open(backup_folder/f"{table_id}.json","w") as json_file:
            json.dump(data, json_file, indent=4)            

    logging.info("Backup completed. Waiting for next backup cycle.")

    # compress
    tar_xz_file=f"{backup_folder}.tar.xz"
    compress_folder_to_tar_xz(backup_folder,tar_xz_file)

    # backup to drive
    upload_to_drive(remote_name, tar_xz_file)
    
    
    # Waiting with status updates
    wait_time = 86400  # 24 hours
    intervals = 12  # Number of intervals to break the wait into
    interval_duration = wait_time / intervals

    for _ in range(intervals):
        time.sleep(interval_duration)
        logging.info("Waiting for the next backup cycle...")

    logging.info("Starting new backup cycle.")





