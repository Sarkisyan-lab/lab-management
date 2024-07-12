# Base Image
FROM python:3.9 
  
# Copy core 
COPY ./synbiobot_CORE /synbiobot_CORE

# Copy bot
COPY ./synbiobot_backup_benchling /synbiobot_backup_benchling

# Remove .env files
RUN rm /synbiobot_CORE/core.env 
RUN rm /synbiobot_backup_benchling/bot.env


# set PATH
ENV PATH="/synbiobot_backup_benchling:${PATH}"

# Set working directory
WORKDIR /synbiobot_backup_benchling

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Install rclone
RUN apt-get update
RUN apt-get install -y rclone

# Command to run the app
CMD ["python", "bot.py"]

