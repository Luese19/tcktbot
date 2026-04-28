# Multi-stage build for Python Telegram bot
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 botuser

FROM base AS builder

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Copy application code
COPY config /app/config
COPY utils /app/utils
COPY handlers /app/handlers
COPY models /app/models
COPY services /app/services
COPY data /app/data
COPY main.py /app/

# Create directories with proper permissions
RUN mkdir -p /app/data/queue /app/data/tickets /app/data/employees /app/data/usernames /app/logs && \
    chown -R botuser:botuser /app && \
    chmod -R 755 /app/logs && \
    chmod -R 755 /app/data

# Switch to non-root user
USER botuser

# Set working directory for runtime
WORKDIR /app

# Health check (optional, checks if process is running)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/proc/1') else 1)"

# Run the bot with proper signal handling
ENTRYPOINT ["python", "-u"]
CMD ["main.py"]
