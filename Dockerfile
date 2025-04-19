# Pull official base image
FROM python:3.12-slim AS builder

# Upgrade pip and install Poetry for managing dependencies
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    pip install --upgrade pip && \
    pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false
RUN poetry install

# Runtime stage
FROM python:3.12-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y

# Copy the virtual environment from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Create a non-root user to run the application
RUN useradd -m appuser

WORKDIR /code
COPY . .

# entrypoint para migraciones
COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "mo.wsgi:application", "--bind", "0.0.0.0:8080"]