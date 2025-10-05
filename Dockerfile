# Use an official lightweight Python image as a base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your data generator and the checker script into the container
# NOTE: We copy the generated data for testing, but in production this will be ignored.
COPY . .

# This is the command that will be run when the container starts
CMD ["python", "run_scheduler_check.py"]
