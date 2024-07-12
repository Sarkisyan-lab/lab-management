# Base Image
FROM python:3.9 

# Update and install dependencies
# RUN apt-get update && apt-get install -y ncbi-blast+
    
# Copy core 
COPY ./synbiobot_CORE /synbiobot_CORE

# Copy bot
COPY ./synbiobot_PCR /synbiobot_PCR

# Remove .env files
RUN rm /synbiobot_CORE/core.env 
RUN rm /synbiobot_PCR/bot.env


# set PATH
ENV PATH="/synbiobot_PCR:${PATH}"

# Set working directory
WORKDIR /synbiobot_PCR

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Command to run the app
CMD ["python", "bot.py"]

