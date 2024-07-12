# Lab-management


This work is licensed under the terms:

GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007

This license is designed to ensure that users have the freedom to run, study, share, and modify the software. Importantly, __any derivative works must also be shared under the same license terms__.

Please cite us :

A platform for lab management, note-keeping and automation<br>
Aubin Fleiss, Alexander S Mishin, Karen S Sarkisyan<br>
bioRxiv 2024.07.08.602487; doi: https://doi.org/10.1101/2024.07.08.602487


Please check the LICENSE file for the full terms.


<br><br><br>
## 1. Introduction
This repository contains a collection of bots running a variety of routine tasks on the database.
Simulating assembly reactions, generating visualisations, summaries, etc. Please check the subfolders for a description of each bot.

The bots are plain python scripts, running in Docker containers.

Most bots require access to an Airtable base to work. Check the section "Creating the database" below for more information.

For some bots, additional requirements apply. You may have to create a [google service account](https://console.cloud.google.com/iam-admin/serviceaccounts) with writing permissions to a google drive folder, and/or the creation of a [Benchling](https://benchling.com/) API key.

<br><br><br>
## 2. How this repository is organised

The folder __synbiobot_CORE__ contains code shared by almost all bots and should always be downloaded.

The other folders, named __synbiobot_[bot name]__ each contain all the code and elements necessary to run a bot. You can choose which bots to run.

<br><br><br>
## 3. Configuration

### Creating the database
In order to run the bots on your database, you will need to create a database with the adequate schema.<br>
The easiest way to do that is to use our template, available from Airtable universe [here](https://www.airtable.com/universe/expPcKlB7VCHE6wVK/lab-management).<br>
You will also need a personal access token from Airtable which you can create [here](https://airtable.com/create/tokens) with read and write permissions on the records of the base and read permission on database schema.

### Populating the .env files
Once this is done, you need to populate the environment files (*.env) in the synbiobot_CORE and synbiobot_[bot name] folders.

core.env contains environment variables shared between bots.<br>
The bot.env files contains additional environment variables specific to each bot. 
Refer to the template env files to learn how to configure your setup.

To help you get started, use the template files (with names ending with ".env.template"). Create a copy of the template file, rename it (the name should end with ".env") and populate the variables inside it.


## 4. Running, stopping and debugging a bot

The helper script called tool_helper.sh can be used to start, stop and open a terminal inside a running Docker container. If you are familiar with Docker you can do it your own way.

Simply open a terminal in the directory of the repo and run this command:

```./tool_helper.sh``` or ```bash tool_helper.sh```


The script will first ask you which bot you wish to select.

Enter the number corresponding to the bot you want and press enter.

The script will then ask what to do with the bot: start it, stop it, enter the terminal, or quit the helper script. 

Enter a number and press enter.

The helper script will then perform the seleted action on the selected bot for you.

<br><br><br>
## 4. Contributing
If you wish to contribute or test something on the code, you can use the tool scripts to assist you.

### tool_setup_dev_envs.sh
This script automates the creation of anaconda environments and the installation of the dependencies required for developing each bot. Run it with the command:

```./tool_setup_dev_envs.sh``` or ```bash tool_setup_dev_envs.sh```


### tool_run_jupyter.sh
This script will ask you to select a bot. It will then activate the required conda environment, load the environment vars and start jupyter notebook for you. Run it with:

```./tool_run_jupyter.sh``` or ```bash tool_run_jupyter.sh```

### tool_refresh_scripts.py
After you have modified the jupyter notebook file(s), use this script to export recursively all jupyter notebook files as python scripts. Run it with the command:

```./tool_refresh_scripts.sh``` or ```bash tool_refresh_scripts.sh```




