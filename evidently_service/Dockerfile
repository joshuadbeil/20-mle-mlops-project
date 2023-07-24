# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

RUN pip install evidently==0.2.8

COPY . /app



CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8085"]