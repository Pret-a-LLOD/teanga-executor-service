#!/bin/bash
service docker start &
python3 dags_generator/generator.py
airflow webserver &
airflow scheduler 
