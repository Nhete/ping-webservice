# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY app.py requirements.txt ./
COPY templates/ ./templates
COPY filtered_hosts.txt ./filtered_hosts.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
