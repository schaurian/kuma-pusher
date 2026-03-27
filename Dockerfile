FROM python:3.14-slim

# Install ping + certs, create unprivileged app user
RUN apt-get update && apt-get install -y --no-install-recommends \
      iputils-ping ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --create-home --home-dir /app app

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

COPY --chown=app:app app.py ./app.py

USER app

ENTRYPOINT ["python", "-u", "app.py"]
