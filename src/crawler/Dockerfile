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

# Copy and filter requirements
COPY requirements.txt /app/

# Create crawler specific requirements - keep only what's needed
RUN grep -E "Crawl4AI|beautifulsoup4|aiohttp|requests|pydantic" requirements.txt > /app/requirements/crawler-requirements.txt

# Add essential dependencies that might not be in requirements.txt
RUN echo "requests>=2.28.0" >> /app/requirements/crawler-requirements.txt

# Install dependencies into a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements/crawler-requirements.txt && \
    pip install --no-cache-dir Crawl4AI

# Runtime stage - Use playwright image with Python support (updated version)
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/venv /app/venv

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Copy the necessary application code
COPY src/ ./src/

# Install any missing packages in the runtime environment
RUN pip install --no-cache-dir requests beautifulsoup4 aiohttp pydantic crawl4ai

# Default command
ENTRYPOINT ["python", "src/insert_docs.py"]
CMD ["--help"]
