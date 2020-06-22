# teanga-client

## Teanga-Client

Teanga uses pre-built docker images available on [docker hub](https://hub.docker.com/u/berstearns) to easily setup and use Teanga-backend([Teanga-backend core](https://github.com/Pret-a-LLOD/teanga-executor-service))

## Requirements

- docker
- access to docker.sock file
- some PORTS should be free:
8080
8000:8000+{numbers_of_services}

## Quick start

```bash
git clone https://github.com/berstearns/teanga-client ./teanga-client
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

## Creating your own workflows

All workflows are created create when you run `[docker-run.sh](http://docker-run.sh)` . It takes all workflows

on the folder `./teanga-client/workflows` and creates airflow workflows (DAGs).

Workflows are a sequence of incrementally numered services. 

In future teanga-frontend will create this workflow.json for the user.

At the moment it's necessary to create it for example:

- operation_id: is the operation you want to run in the service, (you find this information in the openapi-specification of the service)
- input: initial  pre-configurations to be passed to the service
- repo, image_id, image_tag: identfier of the docker hub image
- port: where the service is run on the container
- dependencies: which services this service is dependent on

```bash
{
    "1":{
        "operation_id":"list_top_k",
        "input": {
		"language": "en",
		"number_of_words": 10
        },
        "repo":"berstearns",
        "image_id":"dummy_teanga_service",
        "image_tag":"v0.0.1",
        "port":8001,
        "dependencies": []
    },
    "2":{
        "operation_id":"calculate_word_embeddings",
        "input": {
		"number_of_dimensions": 3
        },
        "repo":"berstearns",
        "image_id":"dummy_teanga_service",
        "image_tag":"v0.0.1",
        "port":8002,
        "dependencies":["1"]
    },
    "3":{
        "operation_id":"calculate_word_embeddings",
        "input": {
		"number_of_dimensions": 300 
        },
        "repo":"berstearns",
        "image_id":"dummy_teanga_service",
        "image_tag":"v0.0.1",
        "port":8003,
        "dependencies":["1"]
    }
}
```

