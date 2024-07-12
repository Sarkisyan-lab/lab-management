#!/bin/bash

directory="."

# Check if Anaconda is installed and available in your PATH
if ! command -v conda &>/dev/null; then
    echo "Anaconda is not found in your PATH. Please install Anaconda or add it to your PATH."
    exit 1
fi

# Function to display the menu
display_menu() {
    echo "Select the environment to activate:"
    local i=1
    for folder in "$directory"/*/; do
        local folder_name=$(basename "$folder")
        echo "$i. $folder_name"
        let i++
    done
    echo "$i. Exit"
}

# Main menu loop
while true; do
    display_menu
    read -p "Enter your choice: " choice
    folders=("$directory"/*/)
    num_folders=${#folders[@]}

    if (( choice < 1 || choice > num_folders )); then
        echo "Exiting..."
        exit 0
    fi

    chosen_bot_env=$(basename "${folders[$choice-1]}")
    break
done

chosen_bot_env="${chosen_bot_env%/}" # removing trailing slash

# Source the Conda environment (assuming anaconda is installed in the default location)
source /home/$(whoami)/anaconda3/etc/profile.d/conda.sh

# Activate the specified Conda environment
conda activate "$chosen_bot_env"

core_env_file="synbiobot_CORE/core.env"
conda_env_file="$chosen_bot_env/bot.env"

echo "Reading $core_env_file"
# Read each line in the core_env_file and set the environment variable
while IFS='=' read -r var value; do
    if [[ -n $var ]]; then
        export "$var"="$value"
        echo "Set $var"
    fi
done < "$core_env_file"

echo "Reading $conda_env_file"
# Read each line in the conda_env_file and set the environment variable
while IFS='=' read -r var value; do
    if [[ -n $var ]]; then
        export "$var"="$value"
        echo "Set $var"
    fi
done < "$conda_env_file"

echo "This python"
echo $(which python)

# Start Jupyter Notebook
jupyter notebook --notebook-dir .
