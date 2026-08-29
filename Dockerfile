FROM python:3.11-slim

WORKDIR /app

# System deps (minimal — sqlite3 is bundled with Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/instance

ENV FLASK_ENV=production
ENV PORT=5000
EXPOSE 5000

# gunicorn with 3 workers is a sane default for a small/medium team.
# The DB is SQLite, so keep workers modest to avoid write contention;
# for higher concurrency, switch DATABASE_URL to Postgres.
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "--timeout", "120", "run:app"]
