FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    procps \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy pyproject.toml and README.md (needed for pip install -e .)
COPY pyproject.toml README.md ./

# Copy source code
COPY src ./src

# Copy other necessary files
COPY run_server.py ./

# Install the package in editable mode
RUN pip install -e .

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=sse
ENV ODOO_TIMEOUT=60
ENV ODOO_VERIFY_SSL=false
ENV PORT=8000
ENV HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "run_server.py"]
