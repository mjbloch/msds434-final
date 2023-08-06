# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

EXPOSE 8080

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . /app

# Set the environment variable for Flask
ENV FLASK_APP=main.py

# Start the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "360", "main:app"]
