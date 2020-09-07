#!/bin/bash
# $1 is the folder to be built and published
IMGID=$(echo $(docker build -qt $1:`date +"%d%m%Y"` $1) | sed "s/sha256://g")
echo "$DOCKERHUB_PASSWORD" | docker login --username=berstearns --password-stdin
docker tag $IMGID berstearns/$1:`date +"%m%Y"` 
docker push berstearns/$1:`date +"%m%Y"`
