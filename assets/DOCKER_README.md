# Docker Setup for RAG with Crawl4AI

This document explains how to run the RAG with Crawl4AI application using Docker, which eliminates the need to install dependencies directly on your machine.

## Prerequisites

Make sure you have at least 10GB of disk space available on your machine. As well as :

- 16GB RAM
- Python 3.13 or higher
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- A model API key.

## Setup

1. Create a `.env` file in the project root with your Google API key:

```sh
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

if you add a model API key make sure to update the `docker-compose.yml` accordingly.

2. Build the Docker images:

```bash
docker-compose build
```

## Usage

### Crawling Websites

Use the provided `crawl.sh` script to crawl websites and store the data in ChromaDB:

```bash
./crawl.sh https://example.com
```

You can pass additional arguments to the crawler:

```bash
./crawl.sh https://example.com --max-depth 2 --collection my_collection
```

Alternatively, you can use docker-compose directly:

```bash
docker-compose run --rm crawler https://example.com --db-dir /data/chroma_db
```

### Running the Streamlit App

Start the Streamlit application:

```bash
docker-compose up -d
```

Then access the application in your browser at: `http://localhost:8501`

### Stopping the Application

```bash
docker-compose down
```

## Data Persistence

The ChromaDB data is stored in a Docker volume named `chroma_data`, which persists across container restarts. This ensures your crawled and embedded data remains available.

## Advanced Usage

### Custom Collection Names

```bash
./crawl.sh https://example.com --collection custom_collection
```

### Adjusting Crawl Parameters

```bash
./crawl.sh https://example.com --max-depth 5 --max-concurrent 20 --chunk-size 1500
```

### Using Different Embedding Models

```bash
./crawl.sh https://example.com --embedding-model all-mpnet-base-v2
```

## Troubleshooting

### Playwright Browser Issues

If you encounter issues with Playwright browsers, you can rebuild the Docker image:

```bash
docker-compose build --no-cache
```

### Memory Issues

If the crawler runs out of memory, try reducing the `--max-concurrent` parameter:

```bash
./crawl.sh https://example.com --max-concurrent 5
```
