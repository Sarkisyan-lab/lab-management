#!/usr/bin/env python
# coding: utf-8

# # Imports

#!/usr/bin/python3

import os 
from os import listdir, mkdir, system
from os.path import isfile, join
import shutil
import sys

import urllib
from random import randint
from time import sleep
from benchlingapi import Session
import json

from Bio import SeqIO
from Bio.SeqFeature import *
from Bio.SeqIO import *
from Bio.Seq import *
import copy
import urllib
import pathlib


# # Constants

verbose=True


try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


benchling_api_key=os.getenv("BENCHLING_API_KEY")
session = Session(benchling_api_key)
#session.DNASequence.one()


# # Functions

def SeqFeature_to_BenchlingFeature(feature):
    new_annot=session.Annotation()
    new_annot.name=feature.qualifiers["label"][0]
    new_annot.start=feature.location.start
    new_annot.end=feature.location.end
    new_annot.strand=feature.strand
    new_annot.type=feature.type
    return(new_annot)

def make_benchling_construct(name,sequence,annotations,is_circular=True):    
    
    # connect to benchling
    folder = session.Folder.find_by_name("Sarkisyan lab DB")
    
    # make dna
    dna = session.DNASequence(
        name = name,
        bases = sequence,
        folder_id = folder.id,
        is_circular = is_circular)

    dna.annotations=annotations
    dna.save()
    
    return(dna)


# # Fetching construcs using non-public links

# adapted from benchlingapi v1 
# see https://pypi.org/project/benchlingapi/1.0/

def encode_dictionary(dictionary):
    for key in dictionary:
        if isinstance(dictionary[key], str):
            dictionary[key] = dictionary[key].encode('utf-8')
        elif isinstance(dictionary[key], dict):
            encode_dictionary(dictionary[key])
    return


def _convert_benchling_features(benchling_seq):
    seqfeatures = []
    for ftr in benchling_seq.annotations:
        # if ftr.end==0, set to plasmid len instead
        if ftr.end==0:ftr.end=benchling_seq.length #xxx
        
        info = \
            dict(location=FeatureLocation(ftr.start, ftr.end), type=ftr.type, strand=ftr.strand,
                 id=ftr.name, qualifiers={
                    'label': ftr.name,
                    'ApEinfo_fwdcolor': ftr.color,
                    'ApEinfo_revcolor': ftr.color,
                    'color': ftr.color
                })
        if info['type'].strip() == '':
            info['type'] = 'misc'
        info = copy.deepcopy(info)
        #encode_dictionary(info)
        seqfeature = SeqFeature(**info)
        seqfeatures.append(seqfeature)
    return seqfeatures

def _clean_seqrecord_features(seqrecord):
    new_feature_set = []
    for f in seqrecord.features:
        if f.type.strip() == '':
            f.type = 'misc'
        if f.location.start < 0:
            continue
        elif f.location.end < 0:
            continue
        new_feature_set.append(f)
    seqrecord.features = new_feature_set

def seqbenchling_to_seqrecord(benchling_seq):
    bseq = benchling_seq
    features = _convert_benchling_features(bseq)
    seq = Seq(bseq.bases)
    
    topology="circular" if bseq.is_circular else "linear"
    kwargs = {
        'description':bseq.name,
        'dbxrefs': bseq.aliases,
        'features': features,
        'annotations': {'full_name': bseq.name.encode('utf-8'),
                        "molecule_type":"DNA",
                        "topology":topology},
        'letter_annotations': None,
        'name':"somename",# str(bseq.name[:10]),
        'id': str(bseq.id)
    }
    
    kwargs = copy.deepcopy(kwargs)
    #encode_dictionary(kwargs)
    for key in kwargs:
        """if isinstance(kwargs[key], str):
            kwargs[key] = kwargs[key].encode('utf-8')"""
    seqrec = SeqRecord(seq, **kwargs)
    _clean_seqrecord_features(seqrec)
    return seqrec


def write_to_gb(seqrecord, filename):
    with open(filename, 'w') as handle:
        SeqIO.write(seqrecord, handle, 'genbank')
        handle.close()



def benchling_to_gb(url,filename,verbose=False):

    if isinstance(filename,pathlib.Path):
        filename=str(filename)
        
    if filename.endswith(".json"):
        filename.replace(".json",".gb")
    elif filename.endswith(".gb"):
        pass
    else:
        filename=f"{filename}.gb"
    
    try : # get from public link
        urllib.request.urlretrieve(url.split("?")[0]+".gb", filename)
        if verbose: print(f"INFO: Fetched construct using shared link")
    except: # login and try again
        try:
            seqbenchling = session.DNASequence.from_share_link(url)
            seqrecord = seqbenchling_to_seqrecord(seqbenchling)
            write_to_gb(seqrecord,filename)
            if verbose:print(f"INFO: Fetched construct using login")

        except:
            raise Exception(f"Could not fetch construct {url}")

    


def get_benchling_json(url,filename):
    """uses benchling construct link and json output filename"""
    
    seqbenchling = session.DNASequence.from_share_link(url)

    if isinstance(filename,pathlib.Path):
        filename=str(filename)
    
    if filename.endswith(".json"):
        pass
    elif filename.endswith(".gb"):
        filename.replace(".gb",".json")
    else:
        filename=f"{filename}.json"
        
    with open(filename,"w") as out:
        out.write(json.dumps(seqbenchling.save_json(),
                             indent=4))




