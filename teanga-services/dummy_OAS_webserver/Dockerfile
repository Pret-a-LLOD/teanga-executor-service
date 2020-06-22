FROM ubuntu:latest
USER root
RUN apt-get update
RUN apt-get install -y tmux vim git
RUN apt-get install -y python-pip python-dev build-essential
RUN apt-get install -y python3-pip python3-dev

WORKDIR /app
copy ./r.txt r.txt
RUN pip3 install -r r.txt
copy ./ /app
RUN chmod +x /app
RUN mkdir /app/output
#CMD ["gunicorn" ,"-w 1" ,"-b 0.0.0.0:4000" ,"webserver:webserver"]
copy ./openapi.yaml /openapi.yaml
CMD ["sh","-c","/app/webserver.sh ${PORT}"]
