#!/usr/bin/env python
# coding: utf-8

import glob
import os
import threading
import time


# Create a lock object
print_lock = threading.Lock()

def convert_to_script(ipynb_file):
    with print_lock:
        print(f"Converting: {ipynb_file}")

    os.system(f'jupyter nbconvert --log-level WARN --no-prompt --to script "{ipynb_file}"')

    with print_lock:
        print(f"Finished converting: {ipynb_file}")

ipynb_files = glob.glob('**/*.ipynb', recursive=True)

threads = []

for ipynb_file in ipynb_files:
    thread = threading.Thread(target=convert_to_script, args=(ipynb_file,))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join()





