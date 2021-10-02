FROM python:3.8.12-bullseye

ENV PYTHONUNBUFFERED=1
ENV SQLALCHEMY_DATABASE_URI_OPEN='postgres://open_qaira:open_qaira@qairamap-open.c6xdvtbzawt6.us-east-1.rds.amazonaws.com:5432/open-qairamap'

WORKDIR /src

COPY requirements.txt /src/
COPY requirements_test.txt /src/

RUN pip install -r requirements.txt -r requirements_test.txt
