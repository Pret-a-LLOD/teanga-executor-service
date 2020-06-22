# Docs

## Teanga-Backend

Teanga backend is the core component of Teanga which coordinates a sequence of services(implemented as docker containers) by matching input and output based on services dependencies. 

## Understanding Teanga-Backend

This repository contains three different parts:

1. [Teanga-backend core](https://github.com/Pret-a-LLOD/teanga-executor-service)
    1.  use this repo if you want to build teanga-backend from scratch
2. [Teanga-backend services](https://github.com/berstearns/teanga_services)
    1. if  you want create teanga-services use this repo to see templates examples
3. [Teanga-backend client](https://github.com/berstearns/teanga-client) (cli):
    1. use this repo if you want to use pre-built teanga docker image in a workflow you have

## Requirements

- docker
- access to docker.sock file
- some PORTS should be free:
8080
8000:8000+{numbers_of_services}

## Quick start

```bash
git clone https://github.com/berstearns/teanga-client.git ./teanga-client
```

```bash
cd ./teanga-client
```

```bash
source docker-run.sh
```

Then airflow should be accessible at [http://localhost:8080](http://localhost:8080) , With a example Teanga workflow.

[]()

![https://i.ibb.co/jyvypZ1/Screenshot-2020-05-08-at-05-16-21.png](https://i.ibb.co/jyvypZ1/Screenshot-2020-05-08-at-05-16-21.png)


## Run Teanga-Backend manually

### building

```bash
git clone https://github.com/Pret-a-LLOD/teanga-executor-service.git ./teanga-core
```

```bash
cd ./teanga-core
```

```bash
docker build -t teanga_backend:v0.0.1 .
```

```bash
docker run -dt --rm --name teanga_backend \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v $PWD/workflows:/teanga/workflows \
           -v $PWD/OAS:/teanga/OAS \
           -e TEANGA_DIR=$PWD \
           -p 8080:8080 \
           teanga_backend:v0.0.1
```

- then acess webserver (localhost:8080)
- You need to have a `workflows/` folder containing the workflows you want to run in the directory you are executing the last command ( the docker run command)


