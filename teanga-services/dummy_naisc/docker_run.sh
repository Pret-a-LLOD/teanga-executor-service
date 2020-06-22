#!/bin/bash
docker run --rm -p 4000:8080 -e PORT=4000 -d dummy_naisc:`date +"%d%m%Y"`
