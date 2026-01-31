# Backend Dockerfile for Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (FFmpeg for audio/video processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ML models during build to avoid download at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" && \
    python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Copy application code
COPY app/ ./app/

# Create storage directories
RUN mkdir -p storage/pdfs storage/audio storage/video storage/extracted

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Cloud Run uses PORT environment variable (default 8080)
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check with longer start period for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/startup || exit 1

# Run application on port 8080 for Cloud Run
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
