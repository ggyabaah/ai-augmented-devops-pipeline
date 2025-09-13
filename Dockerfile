# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency file first for caching
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the source code
COPY . .

# Default command: Train first, then test
CMD ["bash", "-c", "python model/train.py && python model/test.py"]