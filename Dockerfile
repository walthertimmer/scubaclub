# Stage 1: Builder stage
# Use official Python image
FROM python:3.13-slim AS builder

# Create the app directory
RUN mkdir /app

# Set working directory
WORKDIR /app

# Set environment variables
# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# Upgrade pip and install dependencies
RUN pip install --upgrade pip

# Copy the requirements file first (better caching)
COPY requirements.txt /app/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Compile translations
RUN python manage.py compilemessages

# Stage 2: Production stage
FROM python:3.13-slim

# add non-root user
RUN useradd -m -r appuser && \
   mkdir /app && \
   chown -R appuser /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# copy translations
COPY --from=builder /app/scubaclub/locale /app/scubaclub/locale

# Set the working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE ${PORT:-8000}

# define healthcheck with curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health/ || exit 1

# Create entrypoint script for init tasks
COPY --chown=appuser:appuser docker_entrypoint_init.sh /app/
RUN chmod +x /app/docker_entrypoint_init.sh

# Create entrypoint script for main app
COPY --chown=appuser:appuser docker_entrypoint.sh /app/
RUN chmod +x /app/docker_entrypoint.sh

# Default command for main container
CMD ["/app/docker_entrypoint.sh"]

### Start Django application using Gunicorn
# python manage.py ensure_schema && \
# python manage.py makemigrations && \
# python manage.py migrate && \
# python manage.py compilemessages && \
# python manage.py collectstatic --noinput && \
# CMD ["sh", "-c", "\
#     gunicorn scubaclub.wsgi:application\
#      --bind 0.0.0.0:${PORT:-8000}\
#      --workers=1 --threads=4 --timeout=60\
#     "]
