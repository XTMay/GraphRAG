# =========================================
# Smart Home Graph Agent - Docker Build
# =========================================
#
# Multi-stage build for smaller final image.
#
# Usage:
#   docker build -t smart-home-agent .
#   docker run -p 8000:8000 --env-file .env smart-home-agent
#
# Teaching Points:
# - Multi-stage build: separate "install" from "run"
# - Layer caching: requirements.txt copied first (changes less often)
# - Non-root user: security best practice
# - HEALTHCHECK: Docker monitors container health

# =========================================
# Stage 1: Builder - Install Dependencies
# =========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy only requirements first (leverage Docker layer cache)
COPY requirements.txt .

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# =========================================
# Stage 2: Runtime - Copy and Run
# =========================================
FROM python:3.11-slim AS runtime

# Labels for documentation
LABEL maintainer="Smart Home Graph Agent Team"
LABEL description="AI Agent with GraphRAG for smart home control"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Make sure we use the venv's Python
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY data/ ./data/
COPY api_server.py .
COPY app.py .
COPY streamlit_app.py .

# Create non-root user (security best practice)
RUN useradd --create-home appuser
USER appuser

# Expose ports
# 8000 = FastAPI, 8501 = Streamlit
EXPOSE 8000 8501

# Health check (Docker will ping this endpoint periodically)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/api/v1/health'); r.raise_for_status()" || exit 1

# Default command: start the API server
CMD ["python", "api_server.py", "--host", "0.0.0.0"]
