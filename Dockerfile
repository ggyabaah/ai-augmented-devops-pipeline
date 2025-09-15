# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Default command: train + test
CMD ["bash", "-c", "python scripts/train.py && python scripts/test.py"]