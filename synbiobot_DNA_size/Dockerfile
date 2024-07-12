# Base Image
FROM python:3.9 
  
# Copy core 
COPY ./synbiobot_CORE /synbiobot_CORE

# Copy bot
COPY ./synbiobot_DNA_size /synbiobot_DNA_size

# Remove .env files
RUN rm /synbiobot_CORE/core.env 
RUN rm /synbiobot_DNA_size/bot.env


# set PATH
ENV PATH="/synbiobot_DNA_size:${PATH}"

# Set working directory
WORKDIR /synbiobot_DNA_size

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Command to run the app
CMD ["python", "bot.py"]

