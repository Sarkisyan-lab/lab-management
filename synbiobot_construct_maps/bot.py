#!/usr/bin/env python
# coding: utf-8




# # Imports

import os
import sys
from random import shuffle
from time import sleep 
import validators
from natsort import natsorted
import logging
from itertools import combinations
from functools import partial
import tempfile
import pathlib
import requests
import urllib
import re


import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from matplotlib.patches import Wedge, Polygon, Rectangle

import numpy as np


from Bio.Restriction import AllEnzymes
from Bio.Seq import Seq
from Bio import SeqIO


import dna_features_viewer


#from pyairtable import Table, retry_strategy


if os.path.exists('../synbiobot_CORE'):
    sys.path.append('../synbiobot_CORE')

from airtable_config import *
from benchling_tools import benchling_to_gb, SeqFeature_to_BenchlingFeature, make_benchling_construct
from upload_download_functions import *


# # Logging

console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file


# # Constants

api_key = os.environ["AIRTABLE_API_KEY"]
base_id=os.environ["BASE_ID"] # main airtable
table_id=os.environ["SYNBIO_C_table"]


working_dir = pathlib.Path(tempfile.gettempdir())


MoClo_enzymes = ["BpiI","BbsI","BsaI","BsmBI","SbfI","AarI","SapI"]


# # Classes




class ConcentricArcPlotter:
    def __init__(self, title, center=(0, 0), topology="circular"):
        self.center = center
        self.figure, self.ax = plt.subplots(figsize=(10, 10))
        self.base_radius = 1
        self.arcs = []
        self.title= title
        self.topology=topology

    def add_arc(self, inner_radius, start_angle, end_angle, color='b', linestyle='-', thickness=0.1, orientation=None, label=None):
        outer_radius = inner_radius + thickness
        arc_info = {
            'inner_radius': inner_radius,
            'outer_radius': outer_radius,
            'start_angle': start_angle,
            'end_angle': end_angle,
            'color': color,
            'linestyle': linestyle,
            'thickness': thickness,
            'orientation': orientation,
            'label': label,
            'label_color':maximize_contrast(color)
        }
        self.arcs.append(arc_info)

    def plot(self,filename=None, show_plot=False):
        # Remove axes and grid
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.xaxis.set_ticks_position('none')
        self.ax.yaxis.set_ticks_position('none')

        # plot sequence start if linear
        if self.topology=="linear":
            self.ax.plot([0.5,1], [0, 0], color='black', linewidth=0.5) # todo: make this use the base radius

        # Set aspect ratio to 'equal'
        self.ax.set_aspect('equal')

        max_radius = 0
        shift_angle_abs =2
            
        for arc_info in self.arcs:
            
            wedge = Wedge(center=self.center,
                          r=arc_info['outer_radius'],
                          theta1=arc_info['start_angle'],
                          theta2=arc_info['end_angle'],
                          width=arc_info['outer_radius'] - arc_info['inner_radius'],
                          facecolor=arc_info['color'],
                          edgecolor=arc_info['color'])
            self.ax.add_patch(wedge)
            max_radius = max(max_radius, arc_info['outer_radius'])

            # Draw label of the arc
            if arc_info['label'] not in MoClo_enzymes:
                self._draw_arc_label(arc_info['inner_radius'], 
                                     arc_info['thickness'], 
                                     arc_info['start_angle'], 
                                     arc_info['end_angle'], 
                                     arc_info['label'],
                                     arc_info['label_color'])

            # draw label of enzyme
            if arc_info['label'] in MoClo_enzymes:
                enz_label_angle = arc_info['start_angle']
                enz_label_radius = arc_info['inner_radius'] - arc_info['thickness']*2
                
                self.ax.text(enz_label_radius * np.cos(np.radians(enz_label_angle)),
                             enz_label_radius * np.sin(np.radians(enz_label_angle)),
                             arc_info['label'], 
                             rotation=enz_label_angle,
                             verticalalignment='center', horizontalalignment='center') # easy to add overhang if needed, arc_info['overhang']


            # Determine arrowhead positions based on orientation #yyy
            if arc_info['label'] in MoClo_enzymes\
            or arc_info['orientation'] and calculate_feature_length(arc_info) >= shift_angle_abs: 
                radius = arc_info['outer_radius']
                arrow_angle = self._determine_arrow_angle(arc_info['start_angle'], arc_info['end_angle'], arc_info['orientation'], radius)

                if arc_info['orientation']=="-":
                    shift_angle=shift_angle_abs
                if arc_info['orientation']=="+":
                    shift_angle=-shift_angle_abs

                # Create first triangle for the pointy end
                triangle_length = arc_info['thickness'] * 3  # Increase the length for better visibility
                
                triangle1_points = np.array([
                    self._get_arc_endpoint(self.center, radius-arc_info['thickness']/2, arrow_angle),
                    self._get_arc_endpoint(self.center, radius+0.01, arrow_angle+shift_angle),
                    self._get_arc_endpoint(self.center, radius+0.01, arrow_angle)
                ])

                # Create second triangle for the pointy end
                triangle2_points = np.array([
                    self._get_arc_endpoint(self.center, radius-arc_info['thickness']/2, arrow_angle),
                    self._get_arc_endpoint(self.center, radius-arc_info['thickness']-0.01, arrow_angle+shift_angle),
                    self._get_arc_endpoint(self.center, radius-arc_info['thickness']-0.01, arrow_angle)
                ])

                for triangle_points in (triangle1_points,triangle2_points):
                    triangle = Polygon(triangle_points, 
                                       closed=True, 
                                       edgecolor='white', 
                                       facecolor='white', 
                                       zorder=10,
                                       linewidth=1)
                    self.ax.add_patch(triangle)
                
                
        self.ax.text(0, 0, self.title, ha='center', va='center', fontsize=12)
        self.ax.set_xlim((-max_radius - 1, max_radius + 1))
        self.ax.set_ylim((-max_radius - 1, max_radius + 1))

        # Automatically adjust x and y limits based on the arcs
        self.ax.relim()
        self.ax.autoscale_view()
        if show_plot:
            plt.show()
        if filename:
            plt.savefig(filename)

    def _determine_arrow_angle(self, start_angle, end_angle, orientation, radius):
        angular_offset = radius * 0.05  # Adjust the multiplier as needed

        if start_angle <= end_angle:
            return start_angle - angular_offset if orientation == "-" else end_angle + angular_offset
        else:
            return 360 + start_angle - angular_offset if orientation == "-" else end_angle + angular_offset

    def _get_arc_endpoint(self, center, radius, angle):
        center_x, center_y = center
        x = center_x + radius * np.cos(np.deg2rad(angle))
        y = center_y + radius * np.sin(np.deg2rad(angle))
        return x, y

    def _draw_arc_label(self, inner_radius, thickness, start_angle, end_angle, label, label_color, fontsize=8):
        if label:  # Draw label only if it is not None
            label = label[::-1]  # Reverse the label for correct reading order

            # Adjust radius for text placement
            text_radius = inner_radius + thickness / 2

            # Adjust for arcs that cross the 360/0 boundary
            if start_angle > end_angle:
                end_angle += 360

            # Calculate the available angular space
            available_angular_space = end_angle - start_angle

            # Adjust the angular space per character (reduce spacing)
            scaling_factor = 0.03  # Adjust this factor as needed for spacing
            angular_space_per_char = fontsize / (text_radius * np.pi) * (360 / (2 * np.pi)) * scaling_factor
            total_angular_space_required = len(label) * angular_space_per_char

            # Truncate the label if necessary
            if total_angular_space_required > available_angular_space:
                max_label_length = int(available_angular_space / angular_space_per_char)
                if max_label_length<0:
                    max_label_length=0
                label = label[:max_label_length]
                if len(label)<10:
                    label=str()

            # Recalculate the label span after potential truncation
            label_angle_span = len(label) * angular_space_per_char

            # Calculate the start angle for the label
            start_label_angle = start_angle + (available_angular_space - label_angle_span) / 2
            end_label_angle = start_label_angle + label_angle_span

            # Calculate angle step between characters
            angle_step = label_angle_span / max(len(label) - 1, 1)

            for i, char in enumerate(label):
                angle = np.deg2rad(start_label_angle + i * angle_step) % (2 * np.pi)
                x = self.center[0] + text_radius * np.cos(angle)
                y = self.center[1] + text_radius * np.sin(angle)

                # Determine rotation based on position
                rotation_angle = np.degrees(angle) - 90 if end_label_angle - start_label_angle < 180 else np.degrees(angle) + 90
                self.ax.text(x, y, char, color=label_color, fontsize=fontsize, ha='center', va='center', rotation=rotation_angle)






# # functions

get_C_table= partial(get_table, table_id)


# ## Color functions

def n_colors_from_cm(nb_colors,cm=plt.get_cmap('cool')): # viridis
    colors = [ to_hex(cm(i/nb_colors), keep_alpha=False) for i in range(nb_colors)]
    return(colors)


enz_colors = {
    enz:enz_color for (enz,enz_color) in zip(MoClo_enzymes, n_colors_from_cm(len(MoClo_enzymes),cm=plt.get_cmap('viridis')))
}





def plot_color_list(color_list, filename, labels=None):
    """Plots and exports a list of colors to a file with labels."""
    if labels is None:
        labels = [""] * len(color_list)  # Default labels to empty strings if not provided

    fig, ax = plt.subplots(figsize=(len(color_list), 1.5))  # Adjust the figure size to accommodate labels

    # Create a rectangle for each color
    for i, (color, label) in enumerate(zip(color_list, labels)):
        rect = Rectangle((i, 0.5), 1, 1, linewidth=1, edgecolor='none', facecolor=color)
        ax.add_patch(rect)
        ax.text(i + 0.5, 0.25, label, ha='center', va='center')  # Add label below the rectangle

    ax.set_xlim(0, len(color_list))
    ax.set_ylim(0, 2)  # Adjust y-axis to fit labels
    ax.axis('off')  # Turn off axis

    plt.savefig(filename, bbox_inches='tight')  # Save the figure to a file
    plt.close(fig)  # Close the plot to free up memory


enzyme_legend_path=working_dir/"enzyme_legend.png"


plot_color_list(color_list=enz_colors.values(),
                filename=enzyme_legend_path,
                labels=enz_colors.keys())





def invert_hex_color(hex_color):
    # Remove the '#' if present
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]

    # Convert hex to RGB
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    # Invert the RGB values
    r_inv, g_inv, b_inv = 255 - r, 255 - g, 255 - b

    # Convert inverted RGB back to hex
    return f'#{r_inv:02x}{g_inv:02x}{b_inv:02x}'





def maximize_contrast(hex_color):
    # Remove the '#' if present
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]

    # Convert hex to RGB
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    # Calculate luminance
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Determine high contrast color (black for bright colors, white for dark colors)
    # Threshold for this decision can be adjusted; here it's set to the middle value (128)
    contrast_color = '#000000' if luminance > 128 else '#ffffff'

    return contrast_color


# ## Angle functions

def calculate_feature_length(feature):
    if feature["start_angle"] <= feature["end_angle"]:
        return feature["end_angle"] - feature["start_angle"]
    else:
        return 360 - feature["start_angle"] + feature["end_angle"]





def do_arcs_intersect(arc1, arc2):
    # Check if an angle is between two angles, considering wrap around 360 degrees
    def is_angle_between(start_angle, end_angle, check_angle):
        if start_angle <= end_angle:
            return start_angle <= check_angle <= end_angle
        else:
            return check_angle >= start_angle or check_angle <= end_angle

    start_angle1 = arc1["start_angle"]
    end_angle1 = arc1["end_angle"]
    start_angle2 = arc2["start_angle"]
    end_angle2 = arc2["end_angle"]

    # Check if start/end angles of one arc are within the other arc
    if is_angle_between(start_angle1, end_angle1, start_angle2) or \
       is_angle_between(start_angle1, end_angle1, end_angle2) or \
       is_angle_between(start_angle2, end_angle2, start_angle1) or \
       is_angle_between(start_angle2, end_angle2, end_angle1):
        return True

    return False


def position_to_angle(position,sequence_length):
    """Transforms a position in the plasmid into an angle in degrees"""
    return(position*360/sequence_length)


# ## Feature functions

def sort_features_by_length(features_as_angles):
    # Sort the features by length
    sorted_features = sorted(features_as_angles, key=calculate_feature_length, reverse=True)
    return sorted_features


def get_plasmid_topology(genbank_file,verbose=False):
    # Read gb file
    try:
        biopython_record = SeqIO.read(genbank_file, "genbank")
    except:
        logging.exception("Failed to parse genbank file")
        return(False)

    try:
        seq_length = len(biopython_record.seq)
        
        if biopython_record.annotations["topology"]=="circular":
            return("circular")
        else:
            return("linear")
    except:
        logging.exception("Failed to parse sequence topology")
        return(False)





def parse_plasmid(genbank_file,verbose=False):

    # Read gb file
    try:
        biopython_record = SeqIO.read(genbank_file, "genbank")
    except:
        logging.exception("Failed to parse genbank file")
        return(False)

    # Parse topology and convert to dna_features_viewer object
    try:
        seq_length = len(biopython_record.seq)
        seq_topology = get_plasmid_topology(genbank_file)

        record = dna_features_viewer.BiopythonTranslator().translate_record(biopython_record,record_class=seq_topology)
    except:
        logging.exception("Failed to parse sequence topology")
        return(False)

    # Process split features
    try:
        for f in biopython_record.features:
            if f.location_operator=="join":
                biopython_label=f.qualifiers["label"][0]
                new_start=f.location.parts[0].start
                new_end=f.location.parts[-1].end
    
                for i,g in enumerate(record.features):
                    if g.label==biopython_label:
                        record.features[i].start=new_start
                        record.features[i].end=new_end
    except:
        logging.exception("Failed to fix split features")

    # Remove less informative features
    record.features = [f for f in record.features if not f.label.lower().startswith("translation".lower())]
    record.features = [f for f in record.features if not f.label.lower().startswith("primer".lower())]
    record.features = [f for f in record.features if not f.label.lower()=="source"]

    # Format features for plotting
    features_as_angles=list()
    
    for feature in record.features:
        if verbose: print(feature)
        
        new_feature=dict() 
        new_feature['start_angle']= position_to_angle(feature.start,seq_length)
        new_feature['end_angle']= position_to_angle(feature.end,seq_length)

        if feature.strand==1:
            new_feature['orientation']="+"
        elif feature.strand==-1:
            new_feature['orientation']="-"
        else:
            new_feature['orientation']=None
        features_as_angles.append(new_feature)

        new_feature['label'] = feature.label
        
    return(features_as_angles)






def detect_enzyme_sites(genbank_file, enzyme_names): #xxx

    selected_enzymes=[AllEnzymes.get(enzyme_name) for enzyme_name in enzyme_names]
    try:
        biopython_record = SeqIO.read(genbank_file, "genbank")
        seq_length = len(biopython_record.seq)
    except Exception as e:
        logging.exception("Failed to parse genbank file")
        return False

    enzyme_features = []

    for enzyme in selected_enzymes:
        for strand, seq in zip(("+", "-"), (biopython_record.seq, biopython_record.seq.reverse_complement())):
            # Make enzyme pattern
            find = enzyme.elucidate().replace("^", "").replace("_", "")
            for i in range(20, 1, -1):
                find = find.replace("N" * i, "[ACGT]{" + str(i) + "}")

            # Search for sites + their overhangs
            results = [m for m in re.finditer(find, str(seq))] #xxx

            # Save sites
            for r in results:
                if strand == "+":
                    start, end = r.span() #xxx
                else:
                    start = len(biopython_record.seq) - r.span()[1] + 1
                    end = len(biopython_record.seq) - r.span()[0] + 1

                overhang_seq = r.group(0)[enzyme.elucidate().index("^"):enzyme.elucidate().index("_") - 1]
                overhang = overhang_seq if strand == 1 else str(Seq(overhang_seq).reverse_complement())

                enzyme_feature = {
                    "label": str(enzyme),
                    "start": start,
                    "start_angle": position_to_angle(start,seq_length),
                    "end": end,
                    "end_angle": position_to_angle(end,seq_length),
                    "orientation": strand,
                    "overhang": overhang
                }

                # make cutting sites more visible
                if enzyme_feature["orientation"]=="+":
                    enzyme_feature["start_angle"]-=5
                    
                if enzyme_feature["orientation"]=="-":
                    enzyme_feature["start_angle"]-=5 

                enzyme_features.append(enzyme_feature)

            if enzyme.is_palindromic():
                break

    return enzyme_features





# ## Plotting functions

def calculate_suitable_radii(features,verbose=False):
    if not features:
        return []

    # debug overlaps
    for combo in list(combinations(features, 2)):
        arc1,arc2 = combo
        if verbose : print(arc1['label'],arc2['label'],"overlap" if do_arcs_intersect(arc1,arc2) else "do not overlap")

    # Initialize the first ring with the first feature
    rings = {0: [features[0]]}
    features[0]["ring_number"] = 0  # Assign the first feature to the first ring

    # Process the rest of the features
    for feature in features[1:]:
        assigned = False

        # Check each ring to see if the feature fits without overlapping
        for ring_number in sorted(rings.keys()):
            overlap = False
            for existing_feature in rings[ring_number]:
                if do_arcs_intersect(feature, existing_feature):
                    overlap = True
                    break

            if not overlap:
                feature["ring_number"] = ring_number
                rings[ring_number].append(feature)
                assigned = True
                break

        # If the feature doesn't fit in any existing ring, create a new ring
        if not assigned:
            new_ring_number = max(rings.keys()) + 1
            feature["ring_number"] = new_ring_number
            rings[new_ring_number] = [feature]

    return features






def prepare_arcs_for_plotting(features_as_angles, arc_thickness=0.1):
    """Takes as input a list of features with start and end angles
    Returns the feature with the appropriate inner radius to use"""

    # sort features by length
    features_as_angles = sort_features_by_length(features_as_angles)

    # calculate on which radius each feature should be plotted
    features_as_angles = calculate_suitable_radii(features_as_angles)

    # pick one unique color for each
    colors = list(reversed(n_colors_from_cm(len(features_as_angles))))
    shuffle(colors)
    
    # set thickness and color
    for i,feature in enumerate(features_as_angles):
        
        feature["thickness"]=arc_thickness
        feature["color"]=colors[i]
    
    return(features_as_angles)






def prepare_enz_for_plotting(enzymes_as_angles, 
                             arc_thickness=0.05):
    """Takes as input a list of features with start and end angles
    Returns the feature with the appropriate inner radius to use"""
    
    # set thickness and color
    for i,feature in enumerate(enzymes_as_angles):
        
        feature["thickness"]=arc_thickness
        feature["color"]=enz_colors[feature["label"]]
            
    return(enzymes_as_angles)









def plot_plasmid_map(gbfile,base_radius=2,
                     arc_thickness = 0.3,
                     spacing = 0.05,
                     title=None,
                     filename=None):

    if not title:
        title=gbfile

    # instanciate plotter
    plotter = ConcentricArcPlotter(title=title,
                                   topology=get_plasmid_topology(gbfile))
    
    # Central circle
    plotter.add_arc(inner_radius=base_radius,
                    start_angle=0,
                    end_angle=360,
                    color='#8a8a8a',
                    thickness=0.01,
                    orientation=None,
                    label=None)

    # prepare features
    features_as_angles = parse_plasmid(gbfile)
    features_as_angles = prepare_arcs_for_plotting(features_as_angles,
                                                   arc_thickness=arc_thickness)
    # plot features
    for feature in features_as_angles:
    
        feature["inner_radius"] = base_radius + feature["ring_number"]*(arc_thickness+spacing)

        plotter.add_arc(inner_radius=feature.get("inner_radius"),
                        start_angle=feature.get("start_angle"),
                        end_angle=feature.get("end_angle"),
                        color=feature.get("color"),
                        thickness = feature.get("thickness"),
                        orientation=feature.get("orientation"),
                        label=feature.get("label"))
        
    # prepare enzymes
    enzymes_as_angles = detect_enzyme_sites(gbfile,MoClo_enzymes)
    enzymes_as_angles = prepare_enz_for_plotting(enzymes_as_angles,arc_thickness=arc_thickness/2)

    # plot enzymes
    for enz_feature in enzymes_as_angles:
        enz_feature["inner_radius"] = base_radius -spacing -arc_thickness/2

        plotter.add_arc(inner_radius=enz_feature.get("inner_radius"),
                            start_angle=enz_feature.get("start_angle"),
                            end_angle=enz_feature.get("end_angle"),
                            color=enz_feature.get("color"),
                            thickness = enz_feature.get("thickness"),
                            orientation=enz_feature.get("orientation"),
                        label=enz_feature.get("label"))
    
    if filename:
        plotter.plot(filename=filename)











# # Main loop

while True:
	#sleep(10)
	
	# retrieve list of constructs to plot
	try:
		C_table=get_C_table()
		
		C_table_records = C_table.all()
		#C_table_records = [C_table.get("recwrGsERIUu20gln")] # testing
		
		C_table_records = [rec for rec in C_table_records if not rec.get("fields").get("Preview")]
		
		C_table_records = natsorted(C_table_records, key=lambda x: x.get("fields").get("ID"))
		C_table_records.reverse()
		C_table_short = C_table_records[:20] # scan the last 20 constructs
		
		shuffle(C_table_records)
		C_table_rest = [elt for elt in C_table_records if not elt.get("fields").get("Preview")]
		C_table_rest = C_table_records[:20] # re-scan randomly some constructs that do not have a map

		
	except:
		logging.exception("Failed to retrieve constructs to plot.")
		continue

	for C_record in C_table_short + C_table_rest:
		
		# retrieve basic info
		try:
			C_record_ID = C_record.get("fields").get("ID")
			C_record_id = C_record.get("id")
			logging.info(f"Generating map for {C_record_ID}".center(50, '-'))
			url=C_record.get("fields").get("Benchling link (public)","")
			logging.info(f"Checking benchling URL")
		except:
			logging.exception("Failed to retrieve basic construct info.")
		
		# check benchling links
		logging.info("Checking benchling links")
		try:
			if not url:
				logging.warning(f"Construct URL for {C_record_ID} is empty.")
				continue
				
			if not validators.url(url):
				logging.error(f"Invalid construct URL for {C_record_ID}.")
				continue
		except:
			logging.exception("Failed to retrieve benchling link")
			continue

		# download genbank file from benchling
		logging.info("Download plasmid map from benchling")
		try:
			try:
				logging.info(f"Downloading sequence from benchling.")
				url=url.split("?")[0]
				gbfile=working_dir/f"{C_record_ID}.gb"
				urllib.request.urlretrieve(url.replace(" ","")+".gb", gbfile)
			except:
				logging.warning(f"Failed to get {C_record_ID} as a gb file from Benchling publicly. Trying authentication.")
				try:
					benchling_to_gb(url, gbfile)
				except:
					logging.exception(f"Failed to get {C_record_ID} as a gb file from Benchling.")
					continue
		except:
			logging.exception("Failed to retrieve construct map from benchling.")
			continue

		# generate map
		logging.info("Generating plasmid map")

		try:
			path_to_map = working_dir/f"{C_record_ID}.png"
			plot_plasmid_map(gbfile,title=C_record_ID,filename=path_to_map)
		except:
			logging.exception("Failed to generate construct map")
			continue
	
		# upload map
		logging.info("Uploading plasmid map")
		try:
			up = upload_to_drive(remote_name, path_to_map)
		except:
			logging.exception("Failed to upload plasmid map")
			continue
	
		# link map in airtable, along with legend
		logging.info("Linking plasmid map to airtable record")
		try:
			if up:
				C_table.update(C_record_id,{"Preview": [{"url":up}]})
		except:
			logging.exception("Failed to link uploaded map to airtable")

		logging.info("Done.")
		#break # testing


	logging.info("Ready.")
	#break # testing










