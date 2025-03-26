#!/bin/bash

# Script to reset MongoDB container and data

echo "Stopping containers..."
docker-compose down

echo "Removing MongoDB volume..."
docker volume rm silk_exercise_mongo-data

echo "Starting containers..."
docker-compose up -d

echo "Waiting for MongoDB to initialize..."
sleep 5

echo "Checking MongoDB logs..."
docker logs mongo_db

echo "Checking API health..."
curl http://localhost:8000/health

echo "Done! MongoDB has been reset and containers restarted." 