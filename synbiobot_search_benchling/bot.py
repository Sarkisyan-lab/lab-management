#!/usr/bin/env python
# coding: utf-8

#!/usr/bin/python3


# # Logging

import logging


console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file


# # Imports

import os
import re
import validators
from natsort import natsorted
import random
import sys
import time


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')

from airtable_config import *
from benchlingapi import Session





# # Functions

def select_records_to_check(input_list, N):
    # Ensure N is non-negative
    N = max(0, N)

    # Get the last N elements of the list
    last_elements = input_list[-N:]

    # If the list is shorter than N, adjust the number of random elements to pick
    num_random_elements = min(N, len(input_list))

    # Randomly pick elements from the list
    random_elements = random.sample(input_list, num_random_elements)

    # Combine the two lists and return
    return last_elements + random_elements


# # Constants

benchling_api_key=os.getenv("BENCHLING_API_KEY")
session = Session(benchling_api_key)


Benchling_link_field='Benchling link (public)'


C_table_id = os.getenv("TABLE_C_ID")


# # Main loop

while True:

    time.sleep(10)

    # detect benchling constructs named dnaXXXX. (where X is a digit),
    # list the URLs as we go
    try:
        logging.info("Scanning benchling...")
        folder = session.Folder.find_by_name("Sarkisyan lab DB") # folder.list() to list stuff inside the folder

         # careful! the patterns must not overlap
        # otherwise the constucts will be considered duplicated
        # and the URLs will not be considered valid
        patterns=list()
        patterns.append("^dna[0-9]{1,5}$") # dna, number followed by nothing
        patterns.append("^dna[0-9]{1,5}\..*") # dna, number, followed by . then anything
        patterns.append("^dna[0-9]{1,5} .*") # dna, number, space followed by anything
        search_results=dict()
        
        # search the whole contents of the main folder
        for e in folder.all_entities():
        
            for pattern in patterns:
                result=re.search(pattern, e.name)
                if result:
                    actual_dna_name = re.search("^(dna[0-9]{1,5}).*",e.name).group()
                    search_results.setdefault(actual_dna_name,[])
                    search_results[actual_dna_name].append(e.web_url)
        logging.info("done")
    except:
        logging.exception("Failed to detect dna constructs on benchling")
        continue

    # list records to check on airtable
    try:
        logging.info("Checking airtable...")
        C_table = get_table(C_table_id)
        C_table_all = C_table.all()
        C_table_all=natsorted(C_table_all,key=lambda x:x.get("fields").get("ID"))
        
        C_table_all_empty=[rec for rec in C_table_all if not rec.get("fields").get(Benchling_link_field)]
        C_table_all_warning=[rec for rec in C_table_all if not validators.url(str(rec.get('fields').get(Benchling_link_field)))]
        
        records_to_check = select_records_to_check(C_table_all_empty,10) + select_records_to_check(C_table_all_warning,10)
        records_to_check = natsorted(records_to_check,key=lambda x:x.get("fields").get("ID"))
        logging.info("done")
    except:
        logging.exception("Failed to list records to check on airtable")
        continue

    # save construct URL on airtable if the construct has a unique dna name on benchling
    try:
        logging.info("Saving URLs...")
        for C in records_to_check:
            
            
            C_ID=C.get("fields").get("ID")
        
            the_links=search_results.get(C_ID,[])
            
            if len(the_links)==1: # save shared link only if there is exactly one construct with the correct name
                url=the_links[0]
                C_table.update(record_id=C["id"], fields = {Benchling_link_field: url})
                logging.info(f"Found URL for {C_ID}")
                
            elif len(the_links)==0:
                pass # logging.info(f"No URL found for {C_ID}")
                
            elif len(the_links)>1:
                logging.warning(f"Multiple URLs found for {C_ID}!")

        logging.info("done")
    except:
        logging.exception(f"Failed to save {C_ID}'s URL {url}'")

    logging.info("Ready.")




























