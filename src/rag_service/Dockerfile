# Build stage - using Debian instead of Alpine for better Rust support
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies including Rust for ChromaDB
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a requirements directory
RUN mkdir -p /app/requirements

# Copy and filter requirements
COPY requirements.txt /app/

# Create RAG service specific requirements - keep only what's needed
RUN grep -E "fastapi|uvicorn|pydantic|chromadb|sentence-transformers|aiohttp|more-itertools" requirements.txt > /app/requirements/rag-requirements.txt

# Add any missing dependencies that might not be in requirements.txt
RUN echo "more-itertools>=9.1.0" >> /app/requirements/rag-requirements.txt

# Install dependencies into a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements/rag-requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Copy only the necessary application code
COPY src/rag_service/ ./src/rag_service/
COPY src/db/ ./src/db/
COPY src/llm/ ./src/llm/

# Create directory for ChromaDB
RUN mkdir -p /app/chroma_db

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.rag_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
