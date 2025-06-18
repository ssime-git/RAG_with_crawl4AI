# RAG_with_crawl4AI

A dockerized modular Retrieval-Augmented Generation (RAG) system with web crawling capabilities for building AI-powered knowledge bases from websites.

## System Architecture

```sh
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│             │     │             │     │                     │
│  Crawler    │────▶│ RAG Service │◀────│  Streamlit Web App  │
│  (insert_   │     │ (FastAPI)   │     │                     │
│   docs.py)  │     │             │     │                     │
└─────────────┘     └──────┬──────┘     └─────────────────────┘
                           │                       ▲
                           ▼                       │
                    ┌─────────────┐       ┌────────┴──────┐
                    │             │       │               │
                    │  ChromaDB   │       │  LiteLLM API  │
                    │  Vector DB  │       │               │
                    │             │       │               │
                    └─────────────┘       └───────────────┘
```

## System Components

- **Crawler (insert_docs.py)**: Web crawler that extracts content from websites, processes it into chunks, and sends it to the RAG service.
- **RAG Service**: FastAPI microservice that handles document storage, retrieval, and vector embeddings using ChromaDB.
- **Streamlit Web App**: User interface for querying the knowledge base with RAG capabilities.
- **ChromaDB**: Vector database for storing document embeddings and enabling semantic search.
- **LiteLLM API**: API gateway for accessing various LLM providers (like Google's Gemini).

## Inspiration

This project is inspired by the [crawl4AI](https://github.com/crawl4AI/crawl4AI) project, which is a web crawler that can be used to crawl websites and store the content in a ChromaDB database. [This tutorial](https://github.com/coleam00/ottomator-agents/blob/main/crawl4AI-agent-v2/README.md) was used as a reference.


## Example Usage

```sh
python insert_docs.py <URL> [--collection mydocs] [--db-dir ./chroma_db] [--embedding-model all-MiniLM-L6-v2] [--chunk-size 1000] [--max-depth 3] [--max-concurrent 10] [--batch-size 100]
```

### Arguments

* `URL` : The root URL, .txt file, or sitemap to crawl.
* `--collection` : ChromaDB collection name (default: docs)
* `--db-dir` : Directory for ChromaDB data (default: ./chroma_db)
* `--embedding-model` : Embedding model for vector storage (default: all-MiniLM-L6-v2)
* `--chunk-size` : Maximum characters per chunk (default: 1000)
* `--max-depth` : Recursion depth for regular URLs (default: 3)
* `--max-concurrent` : Max parallel browser sessions (default: 10)
* `--batch-size` : Batch size for ChromaDB insertion (default: 100)

Web site to test the scraping : https://scrapeme.live/shop/


### Chunking Strategy
Splits content first by #, then by ##, then by ### headers.
If a chunk is still too large, splits by character count.
All chunks are less than the specified --chunk-size (default: 1000 characters).

### Metadata
Each chunk is stored with:

* Source URL
* Chunk index
* Extracted headers
* Character and word counts

## Docker Deployment

The system is containerized using Docker and can be deployed using Docker Compose. The architecture consists of four main services:

1. **litellm**: LLM API gateway service for accessing language models
2. **rag-service**: FastAPI service for document storage, retrieval and embeddings
3. **rag-app**: Streamlit web application for user interaction
4. **crawler**: Service for running the document insertion process

### Prerequisites

- Docker and Docker Compose installed
- Google API key for Gemini model access (or other LLM provider keys)

### Environment Setup

Create a `.env` file in the project root with the following variables:

```sh
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-2.0-flash  # Or your preferred model
```

### Building and Running

```bash
# Build all services
docker compose build

# Start the entire stack
docker compose up -d

# To insert documents from a URL
docker compose run --rm crawler python src/insert_docs.py https://example.com --rag-service-url http://rag-service:8000
```

### Accessing Services

- Streamlit Web App: http://localhost:8501
- RAG Service API: http://localhost:8000
- LiteLLM API: http://localhost:8008

## RAG Service API Endpoints

### Health Check
```sh
GET /health
```
Returns the health status of the RAG service.

### Document Insertion
```sh   
POST /documents
Content-Type: application/json

{
  "documents": ["document content 1", "document content 2"],
  "metadatas": [{"source": "url1"}, {"source": "url2"}],
  "ids": ["id1", "id2"],
  "collection_name": "docs"
}
```
Inserts documents into the specified ChromaDB collection.

### Document Retrieval
```sh
POST /retrieve
Content-Type: application/json

{
  "query": "your search query",
  "n_results": 5,
  "collection_name": "docs"
}
```
Retrieves relevant documents from the collection based on the query.

### RAG Query
```
POST /rag/query
Content-Type: application/json

{
  "query": "your question",
  "n_results": 5,
  "collection_name": "docs",
  "temperature": 0.7,
  "max_tokens": 1000
}
```
Performs a RAG query, retrieving relevant documents and generating an answer using the LLM.

## Development Workflow

### Project Structure

```sh
.
├── src/
│   ├── crawler/          # Web crawling modules
│   ├── db/               # ChromaDB client and utilities
│   ├── llm/              # LLM client for API interactions
│   ├── rag_service/      # FastAPI RAG service
│   ├── insert_docs.py    # Document crawler and insertion script
│   └── streamlit_app.py  # Streamlit web application
├── Dockerfile           # Main Dockerfile for Streamlit app
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
└── litellm_config.yaml  # LiteLLM configuration
```