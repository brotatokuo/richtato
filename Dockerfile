# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Run the Django development server