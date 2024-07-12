#!/usr/bin/env python
# coding: utf-8

#!/usr/bin/python3


# # Imports

import os 
import logging
from os import listdir, mkdir, system
from os.path import isfile, join
import shutil
import sys
import pathlib
from tempfile import gettempdir
import urllib
from random import randint
from time import sleep
import copy





# from pyairtable import Table

from Bio.Restriction import *
from benchlingapi import Session

import dnacauldron
from geneblocks import CommonBlocks, load_record

from Bio.Restriction import AllEnzymes
from pydna.dseqrecord import Dseqrecord





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

# synbio gg_table
api_key = os.getenv("AIRTABLE_API_KEY")
base_key=os.getenv("BASE_ID")

table_id = os.getenv("TABLE_GG_ID")
C_table_id = os.getenv("TABLE_C_ID")
benchling_api_key=os.getenv("BENCHLING_API_KEY")

if not all([api_key,base_key,table_id,C_table_id,benchling_api_key]):
    raise ValueError("One or more env var is empty")





Scan_result_field="Scan result"
Scan_product_field="Scan product"
Mols_OK_field='Molecules 👌'
Benchling_link_field='Benchling link (public)'
Construct_name_descr_field='Construct name and description'
Construct_to_assemble_field="Construct to assemble"
acceptor_field="Acceptor (C)"
acceptor_RE_field="RE (acceptor)"
other_molecules_field="Other molecules (C)"
other_mols_RE_field="RE (other molecules)"
create_C_tick_field="Create construct"
Mols_OK_suggested_field="👌 mols suggested"
assembly_strategy_field="Assembly strategy"
backbone_field="backbone"
other_parents_field="other parents"





# Accepted MoClo enzymes
MoClo_enzymes = ["BpiI","BbsI","BsaI","BsmBI","SbfI","AarI","SapI"]
MoClo_enzymes_lower=[enz.lower() for enz in MoClo_enzymes]
isosch_sep = " = "


verbose=True


working_dir = pathlib.Path(gettempdir())


# # Functions

get_GG_table= partial(get_table, table_id)
get_C_table= partial(get_table, C_table_id)





def replace_double_space(s):
    while "  " in s:
        s=s.replace("  "," ")
    return(s)





def gg_record_is_complete(gg):
    """Checks if all the necessary info is provided in the gg record"""

    error_msg=str()
    gg_fields=gg.get("fields")
    
    # check that exactly 1 acceptor was provided
    if not len(gg_fields.get(acceptor_field,list()))==1:
        error_msg="Please provide exactly one Acceptor"

    # check if some insert was provided
    if not gg_fields.get(other_molecules_field) :
        error_msg="Please provide at least one insert"

    # check if an enzyme was provided for the acceptor
    if not gg_fields.get(acceptor_RE_field):
        error_msg=f"{acceptor_RE_field}: no enzyme!"

    # check if an enzyme was provided for the inserts
    if not gg_fields.get(other_mols_RE_field):
        error_msg=f"{other_mols_RE_field}: no enzyme!"

    
    # if all good
    if not error_msg:
        return(True)

    # if something is missing
    else:
        gg_table.update(gg["id"], {Scan_result_field: error_msg })
        logging.error(error_msg)
        return(False)





def download_sequence(construct_id, reaction_folder, gg):
    """Downloads a sequence."""

    gg_id = gg.get("id")
    
    # Initialize file path as None
    file_path = None

    try:
        # Fetch record
        record = C_table.get(construct_id)
        url = record.get("fields").get(Benchling_link_field)
        ID = record.get("fields").get("ID")
        file_path = reaction_folder / f"{ID}.gb"

        # Attempt to download the file
        try:
            urllib.request.urlretrieve(url.split("?")[0] + ".gb", file_path)  # works with public links
        except Exception as e:
            benchling_to_gb(url, file_path)  # uses auth for non-public links

    except:
        error_msg = "Could not fetch acceptor, try a public link"
        gg_table.update(gg_id, {Scan_result_field: error_msg})
        logging.exception(error_msg)

    return file_path





def refresh_directory(dir_path):
    """
    Deletes the directory at the specified path if it exists, then recreates it.

    Parameters:
    dir_path (str): The path to the directory to be recreated.
    """
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)





def parse_gb(gb_path, gb_ID):
    """parse gb sequence file"""

    if isinstance(gb_path,pathlib.Path):
        gb_path=str(gb_path)
    
    try:
        seqrec = dnacauldron.biotools.load_record(gb_path) # parse(acceptor_filename, ds=True)[0]
        seqrec.id=gb_ID
        seqrec.name=gb_ID
        
        if seqrec.annotations.get("topology")=="circular":
            seqrec = Dseqrecord(seqrec,circular=True,linear=False)
        else:
            seqrec = Dseqrecord(seqrec,circular=False,linear=True)

        return(seqrec)
            
    except:
        logging.exception("Could not parse gb file.")

        return(None)


def get_record_ID(table, record_id):
    """Returns the ID of the construct found in the constructs table"""
    record_ID = table.get(record_id).get("fields").get("ID")
    return(record_ID)


def enzyme_sort_out_isosch(enz):
    """If the selected enzyme contains the isoschizomere token, split and return the 1rst enzyme name"""
    if isosch_sep in enz: 
        enz=enz.split(isosch_sep)[0]
    return(enz)





def enzyme_is_supported(enz):
    """Checks if a selected enzyme is supported by this script.
    Returns supported enzyme name if yes, False otherwise"""

    enz=enzyme_sort_out_isosch(enz)
    if enz.lower() not in MoClo_enzymes_lower:
        return(False)

    return(True)





def digest_keep_no_site(seqreq, enzyme_name):
    """Digests a Dseqrecord object using supplied enzyme, 
    returns the fragment that contains no recognition site if it is unique.
    Returns False otherwise."""

    try:
        enzyme = AllEnzymes.get(enzyme_name)
        seqreq_dig = [elt for elt in seqreq.cut(enzyme) \
                      if len(enzyme.search(elt.seq))==0 \
                      and len(enzyme.search(elt.seq.reverse_complement()))==0]
        
        # we do not support more than one fragment to assemble per plasmid. But we totally could.
        if len(seqreq_dig)==1:
            return(seqreq_dig[0])
        
    except:
        logging.exception("Could not digest fragment.")
    
    return(False)


def recap_features(seqreq):
    """Returns a list of feature names (list of strings) from the provided seqreq record"""
    
    feature_names=list()
    for feature in seqreq.features:
        try:
            name=feature.qualifiers["label"]
            if not name.startswith("Translation") and not name.startswith("Intron") and "Linker" not in name:
                feature_names.append(name)
        except:
            logging.exception("Failed to summarise a feature name")

    return(feature_names)


def assemble(acceptor_dig, inserts_dig, gg):
    """Attempts assembly from digested acceptor and list of digested interts.
    Return the assembly and an error message (empty if successful)."""

    error_msg=str()
    cloned=acceptor_dig
    gg_ID = gg.get("fields").get("ID")
    
    try:
        # while there are unassembled fragments and attempts left
        tries = 50
        while len(inserts_dig) and tries:
            tries-=1
            insert=inserts_dig.pop().reverse_complement()
            try:
                cloned=cloned+insert
            except:
                inserts_dig.insert(0,insert)

        cloned.name=gg_ID
        cloned.id=gg_ID
        cloned=cloned.looped()

    except Exception:
        error_msg="Assembly failed"
        logging.exception(error_msg)
        
    if len(inserts_dig):
        error_msg = "Not all molecules used in assembly"

    return(cloned,error_msg)








def transfer_features(acceptor, inserts, cloned, gg):
    """Transfers the features found in acceptor and inserts to the assembled product.
    Returns cloned, and an error message
    
    Note: eatures overlapping cutting sites get removed by dnacauldron, we add them back
    Note: dnacauldron adds features to highlight the different parts that were assembled, we remove those
    Note: we also remove duplicate features
    Note: this functions will first remove all features, then add the ones we want.
    """

    gg_ID = gg.get("fields").get("ID")

    error_msg=str()
    try:

        # backup features
        features_bkp = copy.deepcopy(cloned.features)
        
        # remove all features
        cloned.features=[]
        
        # add acceptor features
        blocks = CommonBlocks.from_sequences([acceptor, cloned])
        new_records = blocks.copy_features_between_common_blocks(inplace=True)
        cloned = new_records[gg_ID]
        
        # add insert features
        for insert in inserts:

            blocks = CommonBlocks.from_sequences([insert, cloned])
            new_records = blocks.copy_features_between_common_blocks(inplace=True)
            cloned = new_records[gg_ID] # not sure this is needed, as we are using inplace=True above

        # remove duplicate features
        signatures=list()
        features_to_keep=list()
        for feature in cloned.features:
            signature = (feature.location, feature.qualifiers['label'])
            if signature not in signatures:
                signatures.append(signature)
                features_to_keep.append(feature)

        # assign features again
        if features_to_keep:
            cloned.features=features_to_keep
        else:
            cloned.features=features_bkp
        
    except Exception:
        error_msg="Pass, but post-processing failed"
        logging.exception(error_msg)

    return(cloned,error_msg)





def recap_inserts_transferred_features(acceptor, inserts, cloned):
    """Returns a list of feature names (from the inserts) that were assembled into the product. Very basic implementation"""

    feature_names_in_inserts = list()
    for insert in inserts:
        for feature in insert.features:
            try:
                feature_names_in_inserts.append(feature.qualifiers["label"][0])
            except:
                logging.exception("Could not get feature name")

    feature_names_in_acceptor=list()
    for feature in acceptor.features:
        try:
            feature_names_in_acceptor.append(feature.qualifiers["label"][0])
        except:
            logging.exception("Could not get feature name")
        
    feature_names=list()
    for feature in cloned.features:
        name = feature.qualifiers["label"][0]
        try:
            if name in feature_names_in_inserts \
            and name not in feature_names_in_acceptor:
                feature_names.append(name)
        except:
            logging.exception("Failed to summarise a feature name")

    return(feature_names)





# # Simulate pending reactions

# Note : dnacauldron docs provide example code for a simple/canonical GG example (with only 1 enzyme) but we often use 2 different enzymes, so we proceed step by step: first digest the constructs with their respective enzyme, then assemble the fragments




def simulate_reaction(gg):

    
    # prepare reaction -------------------------------------------------

    # check if the gg record has all the required info
    if not gg_record_is_complete(gg):
        return

    # get basic gg info
    gg_id=gg.get('id')
    gg_ID=get_record_ID(gg_table,gg_id)
    gg_fields=gg.get("fields")
    
    logging.info(f"Simulating {gg_ID}".center(50, "-"))

    
    # refresh reaction dir
    reaction_path = working_dir/gg_ID
    refresh_directory(reaction_path)

    
    # download sequences
    logging.info("Download acceptor")
    acceptor_id = gg_fields.get(acceptor_field)[0]
    acceptor_ID = get_record_ID(C_table,acceptor_id)
    acceptor_path = download_sequence(acceptor_id, reaction_path, gg)

    logging.info("Download other molecules")
    insert_ids = gg_fields.get(other_molecules_field)
    insert_IDs = [get_record_ID(C_table, insert_id) for insert_id in insert_ids]
    insert_paths=[download_sequence(insert_id, reaction_path, gg) \
                  for insert_id in gg_fields.get(other_molecules_field)]

    
    # check download success
    error_msg=str()
    if not acceptor_path:
        error_msg="Could not fetch acceptor, try a public link"
        
    if not all(insert_paths):
        error_msg="Could not fetch insert, try a public link"

    if error_msg:
        logging.error(error_msg)
        gg_table.update(gg_id,{Scan_result_field:error_msg})
        return

    
    # parse downloaded sequences
    logging.info("Parse acceptor")
    acceptor = parse_gb(acceptor_path, acceptor_ID)
    
    logging.info("Parse inserts")
    inserts = [parse_gb(insert_path,gb_ID) for insert_path,gb_ID in zip(insert_paths,insert_IDs)]

    error_msg=str()
    if not acceptor:
        error_msg=f"Could not parse acceptor"

    if not all(inserts):
        error_msg=f"Could not parse insert(s)"

    if error_msg:
        logging.error(error_msg)
        gg_table.update(gg_id, {Scan_result_field: error_msg })
        return

    # check restriction enzymes
    logging.info("Check restriction enzymes")
    acceptor_RE=gg_fields.get(acceptor_RE_field)
    other_mols_RE=gg_fields.get(other_mols_RE_field)

    error_msg=str()
    if not enzyme_is_supported(acceptor_RE):
        msg=f"{acceptor_RE_field}: enzyme not supported"
    acceptor_RE = enzyme_sort_out_isosch(acceptor_RE)

    if not enzyme_is_supported(other_mols_RE):
        msg=f"{other_mols_RE_field}: enzyme not supported"
    other_mols_RE = enzyme_sort_out_isosch(other_mols_RE)

    if error_msg:
        logging.error(error_msg)
        gg_table.update(gg_id, {Scan_result_field: error_msg })
        return

        
    # Digest fragments    
    logging.info("Digesting acceptor")
    acceptor_dig = digest_keep_no_site(acceptor, acceptor_RE)
    inserts_dig = [digest_keep_no_site(insert, other_mols_RE) for insert in inserts] 
    
    error_msg=str()
    if not acceptor_dig:
        error_msg="Could not digest acceptor" # maybe not the most accurate message
    if not all(inserts_dig):
        error_msg="Could not digest insert"

    if error_msg:
        logging.error(error_msg)
        gg_table.update(gg_id, {Scan_result_field: error_msg })
        return        


    # simulate assembly
    logging.info("Simulate assembly")
    cloned, error_msg = assemble(acceptor_dig, inserts_dig, gg)
    
    if error_msg:
        logging.error(error_msg)
        gg_table.update(gg_id, {Scan_result_field: error_msg })
        return
    else:
        msg="Pass"
        logging.info(msg)
        gg_table.update(gg_id, {Scan_result_field: msg })

    
    # transfer features
    logging.info("Adding features to assembled construct")
    cloned, error_msg = transfer_features(acceptor, inserts, cloned, gg)
    if error_msg:
        logging.error(error_msg)
        gg_table.update(gg_id, {Scan_result_field:error_msg})
        return


    # add recap of suitable molecules
    logging.info("Add suggested molecules")
    try:
        msg=str()
        for C_id in gg.get("fields").get(acceptor_field)+ gg.get("fields").get(other_molecules_field):
            C_record = gg_table.get(C_id)
            C_ID = C_record.get("fields").get("ID").strip()
            C_mols_OK = C_record.get("fields").get(Mols_OK_field,"-")
            C_mols_OK = replace_double_space(C_mols_OK).strip().replace(' ',', ')
            msg=f"{msg}* __{C_ID}__: {C_mols_OK}\n"
        gg_table.update(gg_id,{Mols_OK_suggested_field:msg})
        
    except:
        error_msg="Pass, but failed to suggest suitable molecules"
        logging.exception(error_msg)
        gg_table.update(gg_id, {Scan_result_field: error_msg })
        return


    # chekf if user wants to create a construct for the assembly
    if not gg_fields.get(create_C_tick_field,False):
        return

    # create airtable record
    logging.info("Create airtable record")
    try:

        # create construct record in airtable
        new_C = C_table.create({})
        new_C_ID=new_C.get("fields",{}).get("ID")
        logging.info(f"Created new record {new_C_ID}")
        
        # construct name
        inserts_recap = recap_inserts_transferred_features(acceptor, inserts, cloned)
        interts_recap = ", ".join(inserts_recap)
        C_table.update(new_C.get("id"),{Construct_name_descr_field:f"🤖🤖🤖 {interts_recap} cloned into {acceptor_ID}\n"})
        
        # link gg to new construct
        construct_list = gg.get("fields").get(Construct_to_assemble_field,list())
        construct_list.append(new_C["id"])
        gg_table.update(gg_id, {Construct_to_assemble_field: construct_list})
        C_table.update(new_C.get("id"),{assembly_strategy_field:f"Product of {gg_ID}."})
        
        # backbone
        C_table.update(new_C.get("id"),{backbone_field:gg_fields.get(acceptor_field)})
        
        # other parts
        C_table.update(new_C.get("id"),{other_parents_field:gg_fields.get(other_molecules_field)})

    except:
        error_msg="Pass, but failed to create product record on Airtable"
        gg_table.update(gg_id, {Scan_result_field: error_msg })
        logging.exception(error_msg)
        return
    
    # save cloned product to benchling and store link in airtable
    try:
        cloned.features = [feature for feature in cloned.features if feature.qualifiers.get("label",False)]
        # SeqFeature_to_BenchlingFeature crashes if feature has not label
        # only newly created features indicating parts have no label, so we can remove them
        new_annots=[SeqFeature_to_BenchlingFeature(feature) for feature in cloned.features if feature.type!="primer_bind"]
        cloned_benchling = make_benchling_construct(name=new_C_ID,
                                                    sequence=cloned.seq,
                                                    annotations=new_annots,
                                                    is_circular=True)

        C_table.update(new_C.get("id"),{Benchling_link_field: cloned_benchling.web_url})

    except:
        error_msg="Pass, but failed to save product on Benchling"
        gg_table.update(gg_id, {Scan_result_field: error_msg })
        logging.exception(error_msg)
        return

    logging.info("Done")
    sleep(1)


# # Testing




testing=False

if testing:
    gg_table = get_GG_table()
    C_table = get_C_table()
    session = Session(benchling_api_key)
    gg = gg_table.get("recjDUY3nwvshFS9N")
    simulate_reaction(gg)





# # Main

if __name__=="__main__":
    while True:

        try:
            gg_table = get_GG_table()
            C_table = get_C_table()
            session = Session(benchling_api_key)
            
            reactions_to_simulate = gg_table.all()
            reactions_to_simulate = [gg for gg in reactions_to_simulate \
                                     if gg.get("fields").get(Scan_result_field)=="Pending"]
        
            for gg in reactions_to_simulate:
                simulate_reaction(gg)
                
        except:
            error_msg="Main GG loop failed"
            logging.exception(error_msg)

        logging.info("Alive.")
        sleep(10)

























