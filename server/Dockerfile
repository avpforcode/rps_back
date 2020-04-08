FROM python:latest
ADD *.py /server/
ADD /static/* /server/static/
ADD /static/img/* /server/static/img/
WORKDIR /server/
COPY requirements.txt .
RUN pip install -r requirements.txt