# Production-credible backend image: migrations run before serving.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
RUN pip install --no-cache-dir . \
    && rm -rf build *.egg-info \
    && useradd --create-home --shell /usr/sbin/nologin appuser

# Alembic migration tree (needed at container startup).
COPY alembic ./alembic
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

# Apply migrations, then serve. Failing migrations fail the container.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
