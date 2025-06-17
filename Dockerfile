# Playwright browsers are already installed in the base image
FROM mcr.microsoft.com/playwright:v1.52.0-jammy

WORKDIR /app

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python/pip to make them the default
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install uv && \
    uv pip install --system --no-cache-dir -r requirements.txt

# Copy application code and configuration
COPY src/ ./src/
COPY litellm_config.yaml .

# Create directory for ChromaDB
RUN mkdir -p /data/chroma_db

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "src/streamlit_app.py"]
