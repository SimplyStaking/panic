#!/bin/bash
#check whether any configurations exist
subdir_count=$(find ./config/ -maxdepth 1 -type d | wc -l)

if [[ "$subdir_count" -eq 1 ]]
then
  echo "No configurations found. Skipping migration process..."
  exit
fi

#build, wait, kill container
docker-compose up --build -d mongo-startup
docker-compose up --build -d migration
docker exec -it migration pipenv run python config_to_database_migration.py
sleep 5;

echo "Configurations migrated to MongoDB."

#remove migrated configurations
rm -r config/*
