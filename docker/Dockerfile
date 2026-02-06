# Swiss Federal Court Data Generation - Dockerfile
# Multi-stage build for minimal image size and security

# =============================================================================
# Builder stage: Install dependencies
# =============================================================================
FROM python:3.11-slim AS builder

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY README.md .

# Create virtual environment and install dependencies
RUN uv venv /app/.venv
RUN uv sync --no-dev --no-install-project

# =============================================================================
# Final stage: Runtime image
# =============================================================================
FROM python:3.11-slim AS final

# Security: Create non-root user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY pyproject.toml README.md ./

# Create directories for data and output
RUN mkdir -p /app/data /app/output /app/logs && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Health check (optional - remove if not running as service)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import swiss_court_data_gen; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "swiss_court_data_gen.synthetic_data_generation"]
