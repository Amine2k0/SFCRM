# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# Keep Python from writing .pyc files and buffering logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached across code changes.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt && \
    python -m pip install gunicorn==23.0.0

COPY . .

# Run as an unprivileged user. The data dir must exist and be owned by that
# user before the named volume is mounted, so the volume inherits ownership.
RUN adduser --disabled-password --gecos "" --uid 10001 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Apply migrations, then serve. Uses the dev server when DJANGO_DEBUG is on.
CMD ["sh", "-c", "python manage.py migrate --noinput && \
    if [ \"$DJANGO_DEBUG\" = \"True\" ]; then \
      python manage.py runserver 0.0.0.0:8000; \
    else \
      python manage.py collectstatic --noinput && \
      gunicorn SFCRM.wsgi:application --bind 0.0.0.0:8000; \
    fi"]
