# Use official Python slim image
FROM python:3.12-slim

WORKDIR /app

# Copy app files
COPY app.py requirements.txt ./
COPY templates/ ./templates
COPY filtered_hosts.txt ./filtered_hosts.txt

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
