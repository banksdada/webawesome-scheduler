FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Install dependencies first so Docker can cache this layer
COPY packages/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The code lives in /srv/app (the folder name must match "app.main:app" below)
COPY packages/api ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
