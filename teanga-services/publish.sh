#!/bin/bash
# $1 is the docker image id, $2 the name of the image
echo "$DOCKERHUB_PASSWORD" | docker login --username=berstearns --password-stdin
docker tag $1 berstearns/$2:`date +"%m%Y"` 
docker push berstearns/$2:`date +"%m%Y"`
