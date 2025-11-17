FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY core/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy framework code
COPY core/ core/

# NOTE: Generated code (run_cache/) is mounted as a volume at runtime.
# We create a placeholder directory in case the volume isn't mounted,
# but it will be overridden by the volume mount in docker-compose.
RUN mkdir -p run_cache && touch run_cache/__init__.py

# Expose port
EXPOSE 8000

# Run the generated FastAPI app via uvicorn with proper path setup
WORKDIR /app
CMD ["sh", "-c", "cd /app && python3 -c \"import sys; sys.path.insert(0, '/app/run_cache'); from generated_api import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\""]
