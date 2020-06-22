#!/bin/bash
# $1 should be the port on the container the webserver will run
gunicorn -w 1 -b 0.0.0.0:$1 webserver:webserver 
