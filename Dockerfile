# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy app files
COPY app.py requirements.txt ./
COPY templates/ ./templates
COPY filtered_hosts.txt ./filtered_hosts.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your Flask app will run on
EXPOSE 10000

# Run the Flask app
CMD ["python", "app.py"]