#!/usr/bin/env python
# coding: utf-8

# # Imports

import os
import sys
from time import sleep 
import validators

from os import listdir
from os.path import isfile, join
from datetime import date
import shutil
import logging
import pathlib
import tarfile
import lzma
from natsort import natsorted

import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse


import urllib


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')

from airtable_config import *
from benchling_tools import benchling_to_gb, get_benchling_json


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

# synbio airtable credentials
api_key = os.getenv("AIRTABLE_API_KEY")
C_table_id = os.getenv("TABLE_C_ID")


# # Functions

get_C_table= partial(get_table, C_table_id)


def get_file_size_in_bytes(file_path):
    size = os.path.getsize(file_path)
    return size


def compress_folder_to_tar_xz(folder_path, output_file):
    with lzma.open(output_file, "w") as f:
        with tarfile.open(fileobj=f, mode="w") as tar:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    tar.add(file_path, arcname=os.path.relpath(file_path, folder_path))


def list_tar_xz_files(directory):
    return [file for file in os.listdir(directory) if file.endswith(".tar.xz")]

def get_datetime_from_filename(filename):
    timestamp_str = filename.split('_')[1].split('.')[0]
    return parse(timestamp_str)

def get_recent_archives(directory):
    files = list_tar_xz_files(directory)
    sorted_files = sorted(files, key=get_datetime_from_filename, reverse=True)

    last_year = datetime.datetime.now() - relativedelta(years=1)
    last_12_months = [datetime.datetime.now() - relativedelta(months=i) for i in range(1, 13)]
    last_4_weeks = [datetime.datetime.now() - relativedelta(weeks=i) for i in range(1, 5)]
    last_7_days = [datetime.datetime.now() - datetime.timedelta(days=i) for i in range(1, 8)]
    today = datetime.datetime.now().date()

    def get_most_recent(files, dates):
        recent_files = []
        for date in dates:
            recent_file = None
            closest_time_diff = float('inf')
            for file in files:
                file_date = get_datetime_from_filename(file)
                time_diff = (date - file_date).total_seconds()
                if 0 <= time_diff < closest_time_diff:
                    closest_time_diff = time_diff
                    recent_file = file
            if recent_file:
                recent_files.append(recent_file)
        return recent_files

    # Check for today's backups
    todays_backups = [file for file in files if get_datetime_from_filename(file).date() == today]

    keep_archives = list()
    keep_archives.extend(todays_backups)
    keep_archives.extend(get_most_recent(sorted_files, [last_year]))
    keep_archives.extend(get_most_recent(sorted_files, last_12_months))
    keep_archives.extend(get_most_recent(sorted_files, last_4_weeks))
    keep_archives.extend(get_most_recent(sorted_files, last_7_days))

    return keep_archives


# # backup




while True:
    
    # prepare folder
    try:
        now = str(datetime.datetime.now())
    
        backup_folder_main = pathlib.Path("../benchling_backups")
        backup_folder = backup_folder_main/f"benchling_{now}"
        
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)
        
        C_table = get_C_table()
        C_records = C_table.all()
    except:
        logging.exception("Initialisation failed")
        sleep(60)
        continue
    
    
    # download all constructs
    unsaved=list()
    for C_record in C_records:
    
        sleep(0.5)
    
        url=None
    
        C_ID = C_record.get("fields").get("ID")
        url=C_record.get("fields").get("Benchling link (public)","")
    
        saved=False
        if validators.url(url):
    
            # get json if possible
            try:
                get_benchling_json(url, backup_folder/f"{C_ID}.json")
                logging.info(f"Saved {C_ID} as json")
                saved=True
            except:
                logging.exception(f"Failed to save {C_ID} as json")
    
            # attempt to get the gb file
            try:
                benchling_to_gb(url, backup_folder/f"{C_ID}.gb")
                logging.info(f"Saved {C_ID} as gb")
                saved=True
            except:
                logging.exception(f"Failed to save{C_ID} as gb.")
    
        else:
            logging.info(f"Construct {C_ID} does not have a valid URL")
    
        if not saved:
            unsaved.append(str(C_ID))
    
    with open(backup_folder/"unsaved.txt","w") as out:
        out.write("\n".join(unsaved))
    
    
    # compress in archive, then remove downloaded files
    try:
        compress_folder_to_tar_xz(backup_folder, f"{str(backup_folder)}.tar.xz")
        shutil.rmtree(backup_folder)
    except:
        logging.exception("Failed to compress backup folder")


    # upload to google drive
    try:
        upload_to_drive(remote_name, f"{str(backup_folder)}.tar.xz")
    except:
        logging.exception("Failed to backup snapshot to google drive.")

    # keep the...
    # most recent backup from one year ago
    # most recent backup from each of the last 12 months
    # most recent backup from each of the last 4 weeks
    # most recent backup from each of the last 7 days
    # any backup created today
    # remove the rest

    keep_archives.extend(todays_backups)
    keep_archives.extend(get_most_recent(sorted_files, [last_year]))
    keep_archives.extend(get_most_recent(sorted_files, last_12_months))
    keep_archives.extend(get_most_recent(sorted_files, last_4_weeks))
    keep_archives.extend(get_most_recent(sorted_files, last_7_days))
    
    all_backups = list_tar_xz_files(backup_folder_main)
    keep_backups = get_recent_archives(backup_folder_main)

    for backup in all_backups:
        if backup not in keep_backups:
            os.remove(backup)

    sleep(86400) # wait one day










