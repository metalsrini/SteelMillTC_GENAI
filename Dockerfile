FROM python:3.9-slim

WORKDIR /app

# Copy the build script and make it executable
COPY build.sh .
RUN chmod +x build.sh

# Copy requirements file
COPY requirements.txt .

# Run our build script which handles the dependencies
RUN ./build.sh

# Copy the application code
COPY . .

# Ensure the upload and processed directories exist
RUN mkdir -p /var/data/uploads /var/data/processed

# Expose the port the app runs on
EXPOSE 10000

# Command to run the application
CMD ["gunicorn", "app:app", "--config", "gunicorn.conf.py"] 