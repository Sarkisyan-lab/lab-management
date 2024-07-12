#!/usr/bin/env python
# coding: utf-8

# # Imports

import os
import sys
import validators
import time
import urllib
import dnacauldron

from pydna.dseqrecord import Dseqrecord
from pydna.amplify import pcr
from pydna.primer import Primer
import logging


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')

from airtable_config import *
from benchling_tools import benchling_to_gb, SeqFeature_to_BenchlingFeature, make_benchling_construct


# # Logging

console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file





# # Constants

C_table_id = os.getenv("TABLE_C_ID")
C_table_benchling_link_field="Benchling link (public)"
C_table_assembly_strategy_field="Assembly strategy"
C_table_name_desc_field="Construct name and description"
C_table_other_parents_field="other parents"
C_table_is_prod_field="🔁is product of PCR"

M_table_id = os.getenv("TABLE_M_ID")
M_table_template_M_field="Template mol used"
M_table_construct_field="Construct"
M_table_primers_field="Primers"

PCR_table_id = os.getenv("TABLE_PCR_ID")
PCR_table_template_field="Template mol used"
PCR_table_make_C_field="make C"

Primer_table_id= os.getenv("TABLE_PRIMER_ID")
Primer_table_seq_field="Sequence 5' >>> 3'"





verbose=True


# # Functions

get_C_table= partial(get_table, C_table_id)
get_M_table= partial(get_table, M_table_id)
get_PCR_table= partial(get_table, PCR_table_id)
get_Primer_table= partial(get_table, Primer_table_id)


# # List pending PCRs

C_table=get_C_table()
M_table=get_M_table()
PCR_table=get_PCR_table()
Primer_table=get_Primer_table()





# # Simulate PCR

while True:

    try:
        time.sleep(10)
    
        PCRs_to_simulate=[rec for rec in PCR_table.all() if rec.get("fields").get("Status")=="Pending"]
        len(PCRs_to_simulate)
    
        for PCR in PCRs_to_simulate:
            
            PCR_ID=PCR.get("fields",{}).get("ID","")
            PCR_id=PCR.get("id")
            
            # if construct is requested, and no construct is linked
            # and the template and 2 primers are defined, proceed
            
            if PCR.get("fields").get(M_table_template_M_field)\
            and isinstance(PCR.get("fields").get(M_table_primers_field),list)\
            and len(PCR.get("fields").get(M_table_primers_field))==2:
                
                logging.info(f"Simulating {PCR_ID}".center(50, "-"))
                
                # get info of template molecule
                try:
                    template_M=PCR.get("fields",False).get(M_table_template_M_field,False)
                    if not template_M:
                        raise
                    else:
                        template_M=template_M[0]
                        template_M_record = M_table.get(template_M)
                except:
                    msg="Please provide a template molecule"
                    PCR_table.update(PCR_id, {"Status": msg })
                    logging.exception(msg)
                    continue 
                
                # get sequence of the parent construct
                # which we will use as template to simulate the PCR
                try:
                    if not template_M_record.get("fields",False).get(M_table_construct_field,False):raise
                    else:template_C=C_table.get(template_M_record.get("fields").get(M_table_construct_field)[0])
                except:
                    msg="The template molecule is not linked to a construct"
                    PCR_table.update(PCR_id, {"Status": msg })
                    logging.exception(msg)
                    continue
                
                # get template record
                url=template_C.get("fields",False).get(C_table_benchling_link_field,False)
                if not(url and validators.url(url) and url.startswith("https://benchling.com/")):
                    msg="Missing benchling link in template record"
                    PCR_table.update(PCR_id, {"Status": msg })
                    logging.error(msg)
                    continue
                try:
                    url=url.split("?")[0]
                    dna=template_C.get("fields",False).get("ID","")
                    gbfile=f"/tmp/{dna}.gb"
                    try:urllib.request.urlretrieve(url.replace(" ","")+".gb",gbfile)
                    except:
                        try:benchling_to_gb(url,gbfile)
                        except:raise
                except:
                    msg="Could not fetch template construct, try a public link"
                    PCR_table.update(PCR_id, {"Status": msg })
                    logging.exception(msg)
                    continue
                    
                # parse template record
                try:
                    template_gb=dnacauldron.biotools.load_record(gbfile)
                    if template_gb.annotations.get("topology")=="circular":template_gb = Dseqrecord(template_gb,circular=True,linear=False)
                    else:template_gb = Dseqrecord(template_gb,circular=False,linear=True)
                except:
                    msg="Could not parse template construct"
                    PCR_table.update(PCR_id, {"Status": msg })
                    logging.exception(msg)
                    continue
                
                
                # get primers
                try:
                    primers=PCR.get("fields",{}).get("Primers",False)
                    if not primers:raise
                    else:
                        if len(primers)==2:
                            p1=Primer_table.get(primers[0])
                            p1_seq = p1.get("fields",{}).get(Primer_table_seq_field,False)
                            F=Primer(p1_seq)
        
                            p2=Primer_table.get(primers[1])
                            p2_seq=p2.get("fields",{}).get(Primer_table_seq_field,False)
                            R=Primer(p2_seq)
                except:
                    msg="Could not fetch primers"
                    PCR_table.update(PCR_id, {"Status": msg })
                    logging.exception(msg)
                    continue
                
            # simulate PCR
            product=False
            try:
                if template_gb and all ([F,R]):
                    product=pcr(F, R, template_gb)
                    msg="Pass"
                    PCR_table.update(PCR.get("id"), {"Status": msg })
                    logging.info(msg)
            except Exception as e:
                if "PCR not specific" in str(e):msg="Fail: PCR not specific"
                elif "No forward" in str(e) or "No reverse" in str(e): msg="Fail: one primer or more does not anneal"
                elif "No PCR product" in str(e):msg="Fail: No PCR product"
                else:msg="Fail"
                PCR_table.update(PCR_id, {"Status": msg })
                logging.exception(msg)
            
            
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
                f_names=list()
                        
        
            # save to benchling/C_table
            if product and PCR.get("fields",False).get(PCR_table_make_C_field,False):
                try:
                    new_C = C_table.create({})
                    new_C_ID=new_C.get("fields",{}).get("ID")
        
                    new_annots=[SeqFeature_to_BenchlingFeature(feature) for feature in product.features if feature.type!="primer_bind"]
                    dna = make_benchling_construct(name=f"{new_C_ID}. Product of {PCR_ID}",
                                                   sequence=product.seq.watson,
                                                   annotations=new_annots,
                                                   is_circular=False)
                    
                    f_names=list()
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
                        f_names=list()
                        
                    desc=", ".join(f_names)
                    C_table.update(new_C.get("id"),{C_table_benchling_link_field: dna.web_url,
                                                    C_table_name_desc_field:f"🤖🤖🤖 {desc}",
                                                    C_table_assembly_strategy_field:f"Product of {PCR_ID}",
                                                    C_table_other_parents_field:[template_C.get("id")],
                                                    C_table_is_prod_field:[PCR_id]})
        
        
        
                except:
                    msg="Pass, but failed to register product"
                    PCR_table.update(PCR_id, {"Status": msg })
                    logging.exception("msg")
                    continue
            logging.info("Done")
    
        logging.info("Ready.")
    
    except:
        logging.exception("Main loop failed!")
            
            
    




