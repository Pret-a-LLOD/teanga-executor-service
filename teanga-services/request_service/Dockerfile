FROM python:3.7-alpine
USER root
WORKDIR /teanga
copy ./requirements.txt /teanga/requirements.txt
RUN pip3 install -r /teanga/requirements.txt
copy ./ /teanga
RUN chmod +x /teanga
