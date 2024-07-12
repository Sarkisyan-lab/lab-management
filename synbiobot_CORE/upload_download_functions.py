#!/usr/bin/env python
# coding: utf-8

import logging
import shutil
import subprocess
import os
import time
from tempfile import gettempdir
import requests
from pathlib import Path
import json


from dotenv import load_dotenv


# # Logging

console_handler = logging.StreamHandler()  # Console handler
file_handler = logging.FileHandler('log.log')  # File handler

# Configure the logging module
logging.basicConfig(level=logging.INFO,  # Set logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Set log message format
                    datefmt='%Y-%m-%d %H:%M:%S',  # Set date format for log messages
                    handlers=[console_handler, file_handler])  # Log to both console and file


# # Constants

load_dotenv('core.env',override=True)
work_dir = Path(gettempdir())


# # Rclone config

json_filename=os.environ['JSON_FILENAME']

client_secret=os.environ['PRIVATE_KEY_ID']
project_id=os.environ['PROJECT_ID']
private_key=os.environ['PRIVATE_KEY']
client_email=os.environ['CLIENT_EMAIL']
client_id=os.environ['CLIENT_ID']
auth_uri=os.environ['AUTH_URI']
token_uri=os.environ['TOKEN_URI']
auth_provider_x509_cert_url=os.environ['AUTH_PROVIDER_X509_CERT_URL']
client_x509_cert_url=os.environ['CLIENT_X509_CERT_URL']
team_drive=os.environ['TEAM_DRIVE']
root_folder_id=os.environ['ROOT_FOLDER_ID']

remote_name=os.environ['REMOTE_NAME']


secret_json={
    "type": "service_account",
    "project_id": project_id,
    "private_key_id": client_secret,
    "private_key": private_key.replace('\\n','\n'),
    "client_email": client_email,
    "client_id": client_id,
    "auth_uri": auth_uri,
    "token_uri": token_uri,
    "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
    "client_x509_cert_url": client_x509_cert_url,
    "universe_domain": "googleapis.com"
}

secret_json_path = Path(gettempdir())/json_filename

with open(secret_json_path, 'w') as file:
    json.dump(secret_json,file,indent=2)


rclone_config=f"""[{remote_name}]
type = drive
client_id = {client_id}
client_secret = {client_secret}
scope = drive
service_account_file = {secret_json_path}
team_drive = {team_drive}
root_folder_id = {root_folder_id}
"""

rclone_config_filename=f'{remote_name}_rclone.conf'
rclone_config_path=Path(gettempdir())/rclone_config_filename

with open(rclone_config_path, 'w') as file:
    file.write(rclone_config)


# result = subprocess.run(['rclone', '--config', str(rclone_config_path), 'copy', 'bee.png', f"{remote_name}:"], capture_output=True, text=True)





def file_exists_in_remote(remote_name: str, filename: str, verbose:bool=True) -> bool:
    """Check if a file exists in the given remote."""

    try:
        if verbose: logging.info(f"Checking if the file {filename} exists on remote {remote_name}")
        result = subprocess.run(["rclone",'--config',rclone_config_path,"lsf", f"{remote_name}:"], capture_output=True, check=True, text=True)
        # Check if filename is in the list of files. This assumes filenames are unique in the root.
        result_bool = filename in result.stdout.splitlines()
        if result_bool:
            if verbose: logging.info(f"The file {filename} exists on remote {remote_name}.")
            return True
        else:
            if verbose: logging.info(f"The file {filename} does not exist on remote {remote_name}.")
            return False
    except subprocess.CalledProcessError:
        logging.exception(f"Failed to check if the file {filename} exists on remote {remote_name}.")
        return False








def upload_to_drive(remote_name: str, file_path: str, verbose: bool = True, new_filename: str = None) -> str:
    """Uploads the file [file_path] to Google Drive (using rclone remote [remote_name]), and returns the public link."""

    filename = os.path.basename(file_path)
    dest = f"{remote_name}:{filename}"

    # If new_filename is provided, create a temporary copy of the file with the new name
    if new_filename:
        temp_dir = gettempdir()
        temp_file_path = os.path.join(temp_dir, new_filename)
        shutil.copyfile(file_path, temp_file_path)
        file_path = temp_file_path
        dest = f"{remote_name}:{new_filename}"

    # Check and delete remote file if it exists
    if new_filename:
        file_to_delete = new_filename
    else:
        file_to_delete = filename

    if file_exists_in_remote(remote_name=remote_name, filename=file_to_delete, verbose=verbose):
        if verbose: logging.info(f"Deleting existing file on the remote.")
        try:
            subprocess.run(["rclone",'--config',rclone_config_path, "deletefile", f"{remote_name}:{file_to_delete}"], capture_output=True, check=True, shell=False)
            if verbose: logging.info(f"Successfully deleted existing file {file_to_delete} on the remote.")
        except subprocess.CalledProcessError as e:
            logging.exception(f"Failed to delete existing file {file_to_delete} on the remote")
    
    time.sleep(1)
    
    # Copy file
    if verbose: logging.info(f"Copying file {file_path} to the remote {remote_name}.")
    try:
        subprocess.run(["rclone",'--config',rclone_config_path,"copy", file_path, f"{remote_name}:"], capture_output=True, check=True, shell=False)
        if verbose: logging.info(f"Successfully copied the file {file_path} to the remote {remote_name}.")
    except subprocess.CalledProcessError as e:
        logging.exception(f"Failed to copy the file {file_path} to the remote {remote_name}.")
        return None
    time.sleep(1)
    
    # Get public link (retry a few times with a delay)
    public_link = str()
    last_error = str()
    if verbose: logging.info(f"Obtaining public link of file {file_path} on the remote {remote_name}.")
    for i in range(5):
        if not public_link:
            try:
                result = subprocess.run(["rclone",'--config',rclone_config_path, "link", dest], capture_output=True, check=True, text=True, shell=False)
                public_link = result.stdout.strip()
                public_link = public_link.replace("open?", "uc?export=download&")
                if verbose: logging.info(f"Successfully obtained public link of file {file_path} on the remote {remote_name}.")
                return public_link
            except subprocess.CalledProcessError as e:
                last_error = e
                time.sleep(10)
    
    # If the loop completes and public_link is still not set, log the error.
    if not public_link:
        logging.error(f"Failed to obtain public link of file {file_path} on the remote {remote_name}.")
        
    return None


# upload_to_drive(remote_name,'bee.png')

