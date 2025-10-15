FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    procps \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary files for installation
# Using wildcard pattern to ensure all files are copied
COPY pyproject.toml ./
COPY README.md ./
COPY CHANGELOG.md ./
COPY run_server.py ./

# Copy source code
COPY src ./src

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

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "run_server.py"]
