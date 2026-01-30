FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /data
ENV DOT_SPEND_DATA_DIR=/data

# Run the app
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
