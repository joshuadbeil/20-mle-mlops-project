# Use the official Python image as the base image
FROM python:3.10-slim-buster

# Set the working directory
WORKDIR /app

# Set up environment
COPY . /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the files
# COPY . /app/

# MLFLOW Server
ENV MLFLOW_TRACKING_URI="http://34.159.7.88:5000"

# Expose the port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]