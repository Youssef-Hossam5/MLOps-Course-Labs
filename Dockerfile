# Use official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY app/ app/
COPY data/ data/
COPY main.py .

# Install dependencies with retry and cache clearing
RUN pip install --upgrade pip setuptools wheel && \
    pip cache purge && \
    pip install --default-timeout=1000 --no-cache-dir --retries 5 .

# Set environment variable for data directory
ENV DATA_DIR=/app/data

# Expose application port
EXPOSE 8000

# Run app
CMD ["litestar", "--app", "main:app", "run", "--host", "0.0.0.0", "--port", "8000"]