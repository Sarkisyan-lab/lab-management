# Base Image
FROM python:3.9 

# Update and install dependencies
RUN apt-get update && apt-get install -y ncbi-blast+
    
# Copy core 
COPY ./synbiobot_CORE /synbiobot_CORE

# Copy bot
COPY ./synbiobot_GG /synbiobot_GG

# Remove .env files
RUN rm /synbiobot_CORE/core.env 
RUN rm /synbiobot_GG/bot.env


# set PATH
ENV PATH="/synbiobot_GG:${PATH}"

# Set working directory
WORKDIR /synbiobot_GG

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Command to run the app
CMD ["python", "bot.py"]

