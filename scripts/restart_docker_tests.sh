#!/bin/bash
docker-compose -p panic-tests -f docker-compose-tests.yml stop
y | docker-compose -p panic-tests -f docker-compose-tests.yml rm
docker-compose -p panic-tests -f docker-compose-tests.yml up --build -d test-suite