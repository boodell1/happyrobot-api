# Use the official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install Flask
RUN pip install --no-cache-dir flask

# Expose the port Flask will run on
EXPOSE 8080

# Command to run your Flask app directly
CMD ["python", "load_api.py"]

