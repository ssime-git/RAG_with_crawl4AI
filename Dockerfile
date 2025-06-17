# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies including Rust for compatibility
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a requirements directory
RUN mkdir -p /app/requirements

# Copy and split requirements
COPY requirements.txt /app/

# Create production requirements file by removing development packages
RUN grep -v "pytest\|mypy\|black\|flake8\|isort\|pylint" requirements.txt > /app/requirements/requirements-prod.txt

# Install dependencies into a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install production dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements/requirements-prod.txt

# Runtime stage for Streamlit app
FROM python:3.10-slim AS streamlit

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

# Copy application code and configuration
COPY src/ ./src/
COPY litellm_config.yaml .

# Create directory for ChromaDB
RUN mkdir -p /data/chroma_db

# Default command
CMD ["python", "src/streamlit_app.py"]

