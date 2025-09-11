# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy only necessary files
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Now copy the rest of the source files
COPY . .

# Set default command: Train and test the model
CMD ["bash", "-c", "python model/train.py && python model/test.py"]
