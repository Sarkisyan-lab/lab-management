#!/usr/bin/env python
# coding: utf-8

# # Imports

import os
import validators
import time
import urllib
import logging
import sys
# from pydna.assembly import Assembly


console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')

from airtable_config import *
from benchling_tools import benchling_to_gb, SeqFeature_to_BenchlingFeature, make_benchling_construct


# from pydna.parsers import parse
# from pydna.dseqrecord import Dseqrecord
import dnacauldron


# # Constants

C_table_id = os.getenv("TABLE_C_ID")
C_table_Construct_name_descr_field="Construct name and description"
C_table_assembly_strategy_field="Assembly strategy"
C_table_other_parents_field="other parents"
C_table_Benchling_link_field="Benchling link (public)"
C_table_mols_ok_field='Molecules 👌'


GA_table_id = os.getenv("TABLE_GA_ID")
GA_table_Status_field="Status"
GA_table_parts_field="Parts"
GA_table_suggested_mols_field="M suggested"
GA_table_final_C_field="Final construct"


verbose=True


# # Functions

get_C_table= partial(get_table, C_table_id)
get_GA_table= partial(get_table, GA_table_id)


# # Main loop




while True:
    
    time.sleep(10)

    try:
        C_table=get_C_table()
        GA_table=get_GA_table()
        
        GAs_to_simulate=[GA for GA in GA_table.all() if GA.get("fields").get(GA_table_Status_field)=="Pending"]

        for GA in GAs_to_simulate:
            
            GA_ID=GA.get("fields",{}).get("ID","")
            GA_id=GA.get("id")
            logging.info(f"Simulating Gibson assembly {GA_ID}".center(50, '-'))
            
            # check if some parts were provided
            parts = GA.get("fields",{}).get(GA_table_parts_field,False)
            if not parts:
                msg="Please provide at least one part"
                GA_table.update(GA_id, {GA_table_Status_field: msg })
                logging.error(msg)
                continue
            else:
                # get parts
                parts_names=[C_table.get(part).get("fields",{}).get("ID",False) for part in parts]
                parts_descr=[C_table.get(part).get("fields",{}).get(C_table_Construct_name_descr_field,False) for part in parts]
            
            # get part links
            try:
                urls = [C_table.get(part).get("fields",False).get(C_table_Benchling_link_field,False) for part in parts]
                urls = [url.split("?")[0].replace(" ","").replace("/edit","") if (validators.url(url) and url.startswith("https://benchling.com")) else False for url in urls ]
                if not all(urls):raise
            except:
                msg="Missing benchling link in part record"
                GA_table.update(GA_id, {GA_table_Status_field: msg })
                logging.exception(msg)
                continue
                
            # download parts
            gb_paths=[]
            try:
                for url,ID in zip(urls,parts_names):
                    gb_name=f"{ID}.gb"
                    gb_path=f"/tmp/{gb_name}"
                    
                    try:
                        urllib.request.urlretrieve(url+".gb",gb_path)
                        gb_paths.append(gb_path)
                    except:
                        try:
                            benchling_to_gb(url,gb_path)
                            gb_paths.append(gb_path)
                        except:raise
                                
            except:
                msg="Could not get one part, try using a public link"
                GA_table.update(GA_id, {GA_table_Status_field: msg })
                logging.exception(msg)
                continue
            
            # load sequences
            try:
                repository = dnacauldron.SequenceRepository()
                repository.import_records(files=gb_paths, use_file_names_as_ids=True)
            except:
                msg="Failed to parse parts"
                GA_table.update(GA_id, {GA_table_Status_field: msg })
                logging.exception(msg)
                continue
            
            # simulate assembly
            try:
                assembly = dnacauldron.GibsonAssembly(parts=parts_names,name=GA_ID)
                simulation = assembly.simulate(sequence_repository=repository,annotate_parts_homologies=False)
                products=list(simulation.construct_records)
                if len(products)==1:
                    product=products[0]
                    msg="Pass"
                    GA_table.update(GA_id, {GA_table_Status_field: msg })
                    logging.info(msg)
                elif len(products)==0:
                    msg="No product"
                    GA_table.update(GA_id, {GA_table_Status_field: msg })
                    logging.warning(msg)
                    continue
                elif len(products)>1:
                    msg="Multiple products"
                    GA_table.update(GA_id, {GA_table_Status_field: msg })
                    logging.warning(msg)
                    continue
            except:
                msg="Assembly failed"
                GA_table.update(GA_id, {GA_table_Status_field: msg })
                logging.exception(msg)
                continue
                
                
            # if user wants to register the construct
            if GA.get("fields").get("Make C"):
                
                try:
                
                    product.name=product.id
        
                    # create airtable record
                    new_C = C_table.create({})
                    new_C_ID=new_C.get("fields",{}).get("ID")
        
                    # convert product to benchling construct
                    product.features = [feature for feature in product.features if feature.qualifiers.get("label",False)]
                    new_annots=[SeqFeature_to_BenchlingFeature(feature) for feature in product.features \
                                if feature.type!="primer_bind"\
                                and not feature.qualifiers.get("label")[0].startswith("part")]
                    cloned_benchling = make_benchling_construct(name=new_C_ID,
                                                                sequence=product.seq,
                                                                annotations=new_annots,
                                                                is_circular=True)
                    
                    # list features that ended up in the product
                    f_names=[]
                    try:
                        for f in product.features:
                            try:
                                f_name=f.qualifiers["label"][0]
                                if not f_name.startswith("Translation") \
                                and not f_name.startswith("Intron")\
                                and "Linker" not in f_name:
                                    f_names.append(f_name)
                            except:pass
        
                    except:
                        f_names=["some features"]
        
                    # register benchling construct in airtable
                    desc=", ".join(f_names)
                    C_table.update(new_C.get("id"),{C_table_Benchling_link_field: cloned_benchling.web_url,
                                                    C_table_Construct_name_descr_field:f"🤖🤖🤖 {desc}",
                                                    C_table_assembly_strategy_field:f"Product of {GA_ID}",
                                                    C_table_other_parents_field:parts})
                    logging.info(f"Saved result of {GA_ID} as {new_C_ID}.")
        
                    # register new dna construct in Gibson assembly table
        
                    GA_table.update(GA_id,{GA_table_final_C_field:[new_C.get("id")],
                                           GA_table_Status_field:"Pass"})
                    
                except:
                    msg="Pass, but failed to register construct"
                    GA_table.update(GA_id, {GA_table_Status_field: msg })
                    logging.exception(msg)
                    continue
        
                # suggest molecules OK to use
                try:
                    msg=""
                    for part in parts:
                        part_record=C_table.get(part)
                        mols_OK=part_record.get("fields",{}).get(C_table_mols_ok_field,False)
        
                        sep="" if msg=="" else "\n"
                        if mols_OK:
                            msg=f"{msg}{sep}{part_record.get('fields').get('ID')}: {mols_OK}"
                    GA_table.update(GA_id,{GA_table_suggested_mols_field:msg})
                except:
                    msg="Pass, but failed to suggest suitable molecules"
                    GA_table.update(GA_id, {GA_table_Status_field: msg })
                    logging.exception(msg)
                    continue
                    
            logging.info("Ready")
    except:
        logging.exception("Main loop failed")










