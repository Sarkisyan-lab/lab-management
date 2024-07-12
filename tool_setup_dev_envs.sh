#!/bin/bash

# Source the conda.sh script to initialize conda (user-independent)
source /home/$(whoami)/anaconda3/etc/profile.d/conda.sh  # Dynamically fetch the current user's home directory

# Specify the directory containing the folders
directory="."

# Check if Anaconda is installed and available in your PATH
if ! command -v conda &>/dev/null; then
    echo "Anaconda is not found in your PATH. Please install Anaconda or add it to your PATH."
    exit 1
fi

# Function to display the menu
display_menu() {
    echo "Select the environment to install:"
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

    if [ "$choice" -ge 1 ] && [ "$choice" -le "$num_folders" ]; then
        selected_folder=${folders[$choice-1]}
        folder_name=$(basename "$selected_folder")

        echo "================= Setting up $folder_name ================="
        
        # Create an Anaconda environment with the same name as the folder
        conda create --name "$folder_name" python=3.9 -y
        
        # Activate the environment
        conda activate "$folder_name"
        pip install --upgrade pip setuptools
        conda install chardet -y

        
        echo $(which python)
        
        # Install requirements from requirements.txt file (assuming it exists)
        if [ -f "$selected_folder/requirements.txt" ]; then
            pip install -r "$selected_folder/requirements.txt"
        fi
        
        conda install jupyter -y
        conda install ipykernel -y
        python -m ipykernel install --user --name $folder_name --display-name "$selected_folder"

        # Deactivate the environment
        conda deactivate
        
        echo "Created and configured Anaconda environment: $folder_name"

    elif [ "$choice" -eq "$((num_folders+1))" ]; then
        echo "Exiting..."
        break
    else
        echo "Invalid choice. Please enter a valid number."
    fi
done

conda deactivate
