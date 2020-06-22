FROM ubuntu:latest
USER root
RUN apt-get update && apt-get install -y \
    tmux \
    vim \
    git \
    curl \
    python-pip \ 
    python-dev \
    build-essential \
    python3-pip \
    python3-dev \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sL https://deb.nodesource.com/setup_13.x | bash -
RUN apt-get install nodejs
RUN npm install @openapitools/openapi-generator-cli -g
WORKDIR /teanga
copy ./requirements.txt /teanga/requirements.txt
RUN pip3 install -r /teanga/requirements.txt
copy ./ /teanga
RUN chmod +x /teanga
