FROM ubuntu:18.04
USER root
RUN apt-get -y update
RUN apt-get install  -y python3-pip python3-dev
RUN apt-get install -y docker.io

WORKDIR /teanga-core
ENV AIRFLOW_HOME /teanga-core
RUN chmod +x /teanga-core
copy ./pip_requirements.txt /teanga-core/pip_requirements.txt
RUN pip3 install -r pip_requirements.txt
copy ./ /teanga-core
RUN airflow initdb
RUN chmod +x /teanga-core/init.sh
CMD ["./init.sh"]  
