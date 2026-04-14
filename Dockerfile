FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Coolify sets $PORT; default to 8000 locally.
ENV PORT=8000
EXPOSE 8000

# serve.py serves index.html / stickers.json and handles /api/proxy.
CMD ["sh", "-c", "python serve.py ${PORT:-8000}"]
