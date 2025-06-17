#!/bin/bash

# Check if URL is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <URL> [additional args for insert_docs.py]"
  echo "Example: $0 https://example.com --db-dir /data/chroma_db"
  exit 1
fi

# Extract the URL from the first argument
URL=$1
shift

# Build the Docker image if needed
echo "Building Docker image if needed..."
docker-compose build crawler

# Run the crawler with the provided URL and any additional arguments
echo "Starting crawler for URL: $URL"
docker-compose run --rm crawler "$URL" --db-dir /data/chroma_db "$@"
