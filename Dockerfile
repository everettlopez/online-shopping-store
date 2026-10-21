# API image. Build from the project root:  docker build -t shop-api .
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Product images go to a volume so they survive redeploys; mount one here
    UPLOAD_DIR=/data/uploads

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY docker/start-api.sh ./start-api.sh

RUN useradd --create-home --uid 10001 shop \
    && mkdir -p /data/uploads \
    && chown shop /data/uploads \
    && chmod +x start-api.sh
USER shop

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8000\")}/api/health', timeout=4)"

CMD ["./start-api.sh"]
