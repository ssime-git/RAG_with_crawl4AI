# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install uv for faster package installation
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies into a virtual environment
RUN uv pip install --system --no-cache-dir -r requirements.txt \
    && uv pip install --system --no-cache-dir fastapi uvicorn

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application code
COPY . .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.rag_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
