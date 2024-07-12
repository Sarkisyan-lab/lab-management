#!/usr/bin/env python
# coding: utf-8

import logging

# # logging

console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
					datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
					handlers=[console_handler, file_handler])  # Log to both console and file


logging.info("Starting")


from plannotate.annotate import annotate
from plannotate.resources import get_seq_record
from plannotate.bokeh_plot import get_bokeh
from bokeh.plotting import output_file, save
import os
from playwright.sync_api import sync_playwright
from bokeh.plotting import figure, show
from bokeh.models import Title

from bokeh.plotting import figure, show
from bokeh.models import Label, LabelSet, Title, Annotation

import asyncio
from playwright.async_api import async_playwright
import logging
import sys
from functools import partial
from Bio import SeqIO
from tempfile import gettempdir
import pathlib
import time
from natsort import natsorted
from random import shuffle
import validators
import urllib
import requests

from pyairtable import Table, retry_strategy


if os.path.exists('../synbiobot_CORE'):
	sys.path.append('../synbiobot_CORE')

from airtable_config import *
from benchling_tools import benchling_to_gb, SeqFeature_to_BenchlingFeature, make_benchling_construct
from upload_download_functions import *

# # Constants

api_key = os.environ["AIRTABLE_API_KEY"]
base_id=os.environ["BASE_ID"] # main airtable
table_id=os.environ["SYNBIO_C_table"]


working_dir = pathlib.Path(gettempdir())


# # Functions

def set_text_font_sizes(plot, text_size='30pt', title_size='30pt', axis_label_size='30pt', major_label_size='30pt', legend_label_size='30pt'):
	# fix this function later so that the feature labels are bigger
	
	# Set title font size
	if plot.title:
		plot.title.text_font_size = title_size

	# Set axis labels font size
	plot.xaxis.axis_label_text_font_size = axis_label_size
	plot.yaxis.axis_label_text_font_size = axis_label_size

	# Set major labels font size
	plot.xaxis.major_label_text_font_size = major_label_size
	plot.yaxis.major_label_text_font_size = major_label_size

	# Set legend font size, if legend is present
	if plot.legend:
		plot.legend.label_text_font_size = legend_label_size

	# Set other text elements like annotations or labels
	for render in plot.renderers:
		if isinstance(render, Label) or isinstance(render, LabelSet):
			render.text_font_size = text_size
		elif isinstance(render, Annotation):
			render.text_font_size = text_size



async def capture_screenshot(html_outfile_abs):
	async with async_playwright() as p:
		browser = await p.chromium.launch()
		page = await browser.new_page()

		# Set a large viewport size
		await page.set_viewport_size({"width": 1920, "height": 1080})

		await page.goto(f'file://{html_outfile_abs}')

		# You may need to wait for the plot to fully load
		# await page.wait_for_timeout(5000)  # wait for 5 seconds, adjust as needed

		# Take a screenshot of the full page
		await page.screenshot(path=str(html_outfile_abs).replace("html","png"), full_page=True)
		await browser.close()


get_C_table= partial(get_table, table_id)


# # Main loop




while True:
	
	
	C_table=get_C_table()
	
	all_png_outfile_abs=list()
	all_html_outfile_abs=list()
	all_gbfiles=list()

	try:
		
		logging.info("Retrieving records")
		C_table=get_C_table()
		C_table_records = C_table.all()
		
		
		logging.info("Filtering records")
		C_table_records=[rec for rec in C_table_records if not rec.get("fields").get("pLannotate")]
		
		if not len(C_table_records):
			logging.info("Nothing to do!")
			
		# get last 20 elements
		C_table_records = natsorted(C_table_records, key=lambda x: x.get("fields").get("ID"))
		C_table_records.reverse()
		C_table_short = C_table_records[:20]

		# get 20 additional elements without a map to scan
		shuffle(C_table_records)
		C_table_rest = [elt for elt in C_table_records if not elt.get("fields").get("pLannotate")]
		C_table_rest = C_table_records[:20]
			
		for C_record in C_table_short + C_table_rest:

			dna=C_record.get("fields").get("ID")
			dna_id = C_record.get("id")
			logging.info(f"Generating map for {dna}".center(50, '-'))
			
			#print("=======================")
			#print(C_record.get("fields").get("pLannotate"))
			#print("=======================")

			# ensure construct URL is not empty
			# ensure construct URL is indeed an URL
			logging.info(f"Checking benchling URL")
			url=C_record.get("fields").get("Benchling link (public)","")
			if not url:
				logging.warning(f"Construct URL for {dna} is empty.")
				continue
				
			if not validators.url(url):
				logging.error(f"Invalid construct URL for {dna}.")
				continue
		
			# get the map from Benchling
			try:
				logging.info(f"Downloading sequence from benchling.")
				url=url.split("?")[0]
				gbfile=working_dir/f"{dna}.gb"
				all_gbfiles.append(str(gbfile))
				urllib.request.urlretrieve(url.replace(" ","")+".gb", gbfile)
			except:
				logging.warning(f"Failed to get {dna} as a gb file from Benchling publicly. Trying authentication.")
				try:
					benchling_to_gb(url, gbfile)
				except:
					logging.exception(f"Failed to get {dna} as a gb file from Benchling.")
					continue
					
			logging.info(f"Reading genbank file.")
			try:
				# parse raw sequence and topology
				biopython_record = SeqIO.read(gbfile, "genbank")
				circular = biopython_record.annotations["topology"]=="circular"
				linear=not circular
			except:
				logging.exception("Failed to read gb file.")
				continue
			try:
				if len(biopython_record.seq)>20000:
					logging("Sequence is larger than 20kb, skipping")
					continue
			except:
				logging.exception("Failed to read construct length")
				continue
			
			logging.info(f"Rendering map using pLannotate")
			# Create the plot and save as HTML
			try:
				seq = str(SeqIO.read(gbfile, "genbank").seq).lower()
				logging.info(f"The sequence is {len(seq)} bp long.")
				hits = annotate(seq, is_detailed=True, linear=linear)
				seq_record = get_seq_record(hits, seq)
				plot = get_bokeh(hits, linear=True)
				
				set_text_font_sizes(plot)
				
				html_outfile_abs = working_dir/f"{dna}.html"
				output_file(html_outfile_abs)
				save(plot)
			except:
				logging.exception("Failed to render sequence as bokeh plot")
			
			# export image file
			logging.info(f"Converting html map to png using playwright.")
			try:
				# this runs in python but not in jupyter
				asyncio.run(capture_screenshot(html_outfile_abs))
			except:
				logging.exception("Failed to take screenshot!")
				continue
				
			
			# upload the file
			try:
				logging.info(f"Uploading the file.")
				png_outfile_abs = working_dir/f"{dna}.png"
				up = upload_to_drive(remote_name, str(png_outfile_abs))
				if not up:
					logging.error(f"The URL of {dna}'s map is empty.")
					continue
			except:
				logging.exception("Failed to upload the file")
				continue
			
			# update airtable
			try:
				logging.info(f"Linking image to the airtable record.")
				C_table.update(dna_id,{"pLannotate": [{"url":up}] }) # to upload more than one file,use[{"url":up1},{"url":up2}]
				logging.info(f"Finished rendering {dna}".center(50, '-'))
			except:
				logging.exception("Failed to link uploaded file to airtable")
				continue
			
			try:
				all_png_outfile_abs.append(str(png_outfile_abs))
				all_html_outfile_abs.append(str(html_outfile_abs))
			except:
				pass
			
	except:
		logging.exception("Main loop failed.")
		
	
	# clean up
	for elt in all_png_outfile_abs + all_html_outfile_abs + all_gbfiles:
		try:
			os.remove(elt)
		except:
			logging.warning(f"Failed to clean up {elt}")
	
	logging.info("Ready.")
	time.sleep(30)

	











