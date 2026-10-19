FROM python:3.12-slim

# Install system fonts and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-core \
    fonts-noto-extra \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY . .

# Expose default API server port
EXPOSE 8000

# Default command starts the FastAPI admin service
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
