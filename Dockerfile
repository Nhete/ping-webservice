# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application code and requirements
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your Flask app will run on
EXPOSE 10000

# Start the web service
CMD ["python", "app.py"]
