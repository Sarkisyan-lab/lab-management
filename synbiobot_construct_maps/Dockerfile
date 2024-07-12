# Base Image
FROM python:3.9 
  
# Copy core 
COPY ./synbiobot_CORE /synbiobot_CORE

# Copy bot
COPY ./synbiobot_construct_maps /synbiobot_construct_maps

# Remove .env files
RUN rm /synbiobot_CORE/core.env 
RUN rm /synbiobot_construct_maps/bot.env


# set PATH
ENV PATH="/synbiobot_construct_maps:${PATH}"

# Set working directory
WORKDIR /synbiobot_construct_maps

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Install rclone
RUN apt-get update
RUN apt-get install -y rclone


# Command to run the app
CMD ["python", "bot.py"]

