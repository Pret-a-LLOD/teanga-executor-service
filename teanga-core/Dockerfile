FROM ubuntu:18.04
USER root
RUN apt-get -y update
RUN apt-get install  -y python3-pip python3-dev
RUN apt-get install -y docker.io

WORKDIR /teanga
ENV AIRFLOW_HOME /teanga
RUN chmod +x /teanga
copy ./pip_requirements.txt /teanga/pip_requirements.txt
RUN pip3 install -r pip_requirements.txt
copy ./ /teanga
RUN airflow initdb
RUN chmod +x /teanga/init.sh
CMD ["./init.sh"]  
