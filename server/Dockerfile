FROM python:3.10

WORKDIR server

COPY requirements.txt .

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

WORKDIR app