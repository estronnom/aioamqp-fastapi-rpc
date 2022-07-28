FROM python:3.8

WORKDIR app

COPY requirements.txt .

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

COPY /${APP} .

CMD python3 -u ${APP}/app.py

