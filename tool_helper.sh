#!/bin/bash

clear

# SELECTING A BOT
# ----------------------------------------------

# Get a list of directories in the current folder that start with "synbiobot_" but exclude "synbiobot_CORE"
directories=($(find . -maxdepth 1 -type d -name 'synbiobot_*' ! -name 'synbiobot_CORE' | sort))

# Check if there are any directories
if [ ${#directories[@]} -eq 0 ]; then
    echo "No bot directories found in the current folder."
    exit 1
fi

# Display numbered options for the directories without "./" prefix
echo "Select a bot by entering the corresponding number:"
echo ""
for i in "${!directories[@]}"; do
    dir="${directories[i]#./}"  # Remove the "./" prefix
    echo "$((i+1)). $dir"
done

# Read the user's choice
echo ""
read -p "Enter the number of the bot you want to select: " choice

# Validate the user's input
if ! [[ "$choice" =~ ^[0-9]+$ ]]; then
    echo "Invalid input. Please enter a valid number."
    exit 1
fi

# Check if the chosen number is within the valid range
if [ "$choice" -lt 1 ] || [ "$choice" -gt "${#directories[@]}" ]; then
    echo "Invalid choice. Please enter a number within the valid range."
    exit 1
fi

# Get the selected directory based on the user's choice and remove leading "./"
selected_bot="${directories[$((choice-1))]#./}"

# Now you can use the $selected_bot variable for further actions
echo ""
echo "You selected: $selected_bot"



# SELECTING AN ACTION
# ----------------------------------------------


# Function to display the menu
echo ""
display_menu() {
    echo "What would you like to do?"
    echo ""
    echo "1. Start bot"
    echo "2. Open bot terminal"
    echo "3. Stop bot"
    echo "4. Quit"
    echo ""
    echo -n "Enter your choice (1/2/3/4): "
}

# Loop until a valid choice (1, 2, 3, or 4) is entered
display_menu  # Display the menu
read choice   # Read the user's input

case "$choice" in
	1)
		echo "Starting $selected_bot..."
		docker pull python:3.9		
		docker build --no-cache -f $selected_bot/Dockerfile -t "${selected_bot,,}_img" .

        if [ "$selected_bot" = "synbiobot_backup_airtable" ] || [ "$selected_bot" = "synbiobot_backup_benchling" ]; then

            docker run -d --name $selected_bot --restart=always --env-file ./synbiobot_CORE/core.env --env-file ./$selected_bot/bot.env -v backups:/backups "${selected_bot,,}_img"
        else
            docker run -d --name $selected_bot --restart=always --env-file ./synbiobot_CORE/core.env --env-file ./$selected_bot/bot.env "${selected_bot,,}_img"
        fi
		;;
		
		
		
	2)
		echo "Opening $selected_bot terminal..."
		docker exec -it $selected_bot /bin/bash
		;;
		
		
		
	3)
	
	
	    # Ask the user to confirm
        echo -n "Are you sure you want to stop the bot? Type 'yes' to confirm: "
        read confirmation
        if [ "$confirmation" != "yes" ]; then
            echo "Stopping aborted."
            exit
        fi
        
		echo "Stopping $selected_bot..."

		# Stop the container
		echo "Stopping container..."
		docker stop $selected_bot

		# Wait for the container to fully stop
		sleep 5

		# Remove the container
		echo "Removing container..."
		docker rm $selected_bot

		# Remove the image
		echo "Removing image..."
		docker rmi "${selected_bot,,}_img"

		# Optional: Add a check to ensure the image is removed
		if [[ "$(docker images -q ${selected_bot,,}_img 2> /dev/null)" == "" ]]; then
		  echo "Image removed successfully."
		else
		  echo "Failed to remove the image."
		fi
		;;
		
		
	4)
		echo "Exiting..."
		exit 0  # Exit the script for Option 4
		;;
	*)
		echo "Invalid choice. Please enter 1, 2, 3, or 4."
		;;
esac




