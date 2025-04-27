# Use a small Python base image
FROM python:3.10-slim

# Create a working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your source code
COPY . /app

# Expose the port Flask will listen on
ENV PORT 8080
EXPOSE 8080

# If you typically run "python app.py", do so:
CMD ["python", "app.py"]
