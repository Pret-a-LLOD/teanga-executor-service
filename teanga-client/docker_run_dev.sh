#!/bin/bash
if [ -z "$PWD" ]
then
      echo "\$PWD is empty, trying to set $PWD with $(PWD)"
      PWD=$(pwd)
else
      echo "\$PWD is NOT empty, so using it as base_folder"
fi
mkdir -p IO
mkdir -p OAS
docker run -dt --rm --name teanga_backend \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v $PWD/workflows:/teanga/workflows \
           -v $PWD/OAS:/teanga/OAS \
           -e TEANGA_DIR=$PWD \
           -p 8080:8080 \
           teanga_backend:dev
