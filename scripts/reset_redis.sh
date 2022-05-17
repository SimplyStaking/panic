#!/bin/bash
docker-compose kill redis
docker-compose rm -v redis
docker-compose up --build -d redis