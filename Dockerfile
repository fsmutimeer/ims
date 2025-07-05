# syntax=docker/dockerfile:1

# --- Builder stage ---
FROM python:3.11-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# --- Final stage ---
FROM python:3.11-slim
WORKDIR /app

# System dependencies for psycopg2/mysqlclient (optional, for future DB support)
RUN apt-get update && \
    apt-get install -y libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN pip install --no-cache-dir --find-links=/wheels -r requirements.txt

# Copy project files
COPY . /app/

# Copy .env file for environment variables
COPY .env /app/.env

# Expose port
EXPOSE 8000

# Set environment variables for Django (add more as needed)
ENV DJANGO_SETTINGS_MODULE=mobile_accessories.mobile_accessories.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Default: use SQLite. For MySQL/Postgres, override env vars at runtime.
# Example for Postgres:
# ENV DATABASE_URL=postgres://user:password@host:5432/dbname

# Run the Django development server
CMD ["python", "mobile_accessories/manage.py", "runserver", "0.0.0.0:8000"]
