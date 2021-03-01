docker-compose -p panic-tests -f docker-compose-tests.yml stop
docker-compose -p panic-tests -f docker-compose-tests.yml rm
docker-compose -p panic-tests -f docker-compose-tests.yml up --build -d test-suite