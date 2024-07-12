#!/usr/bin/env python
# coding: utf-8

# # Imports

import os
import sys
import re
from random import shuffle,randint
import time
import validators
from Bio import SeqIO
import urllib
import logging


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')

from airtable_config import *
from benchling_tools import benchling_to_gb


# # Logging

console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file


# # Constants

api_key = os.getenv("AIRTABLE_API_KEY")
base_key=os.getenv("BASE_ID")

C_table_id = os.getenv("TABLE_C_ID")
benchling_api_key=os.getenv("BENCHLING_API_KEY")

if not all([api_key,base_key,C_table_id,benchling_api_key]):
    raise ValueError("One or more env var is empty")


get_C_table= partial(get_table, C_table_id)


# # Main




while True:

    try:

        C_table = get_C_table()

        C_table_records = C_table.all()
        C_table_records = sorted(C_table_records, key=lambda x:int(x.get("fields").get("ID").replace("dna","")))
        C_table_records.reverse()
        
        C_table_no_size = [elt for elt in C_table_records if not elt.get("fields").get("size")]
        C_table_has_size = [elt for elt in C_table_records if elt.get("fields").get("size")]
        
        # subsample a few records to update that already have a length
        shuffle(C_table_has_size)
        C_table_has_size = C_table_has_size[:20]

    
        for C_record in C_table_no_size+C_table_has_size:

            dna= C_record.get("fields").get("ID")
            url=None

            logging.info(f"Checking {dna}")
                
            dna=C_record.get("fields").get("ID")
            gbfile=f"/tmp/{dna}.gb"
            url=C_record.get("fields").get("Benchling link (public)","")
            if validators.url(url) :
                # this is the slow bit
                url=url.split("?")[0]
                try:
                    urllib.request.urlretrieve(url.replace(" ","")+".gb", gbfile)
                except:
                    try:
                        benchling_to_gb(url,gbfile)
                    except:
                        gbfile=None
        
                try:
        
                    biopython_record = SeqIO.read(gbfile, "genbank")
                    seq_len = len(biopython_record)
                    C_table.update(C_record.get("id"),{'size':seq_len})
        
                except :
                    logging.exception(f"ERROR {dna} Could not calculate sequence size.")
            
            time.sleep(1)
    except:
        logging.exception("Main loop failed")

    logging.info("Alive")
    time.sleep(10)
    










