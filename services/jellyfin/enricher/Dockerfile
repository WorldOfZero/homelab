FROM python:3.13-slim

# tzdata so RUN_AT is interpreted in the container's TZ
RUN pip install --no-cache-dir pyyaml==6.0.2 tzdata==2025.2

WORKDIR /app
COPY enricher.py config.yaml auto-collections.json ./
COPY collection-images/ ./collection-images/

USER 1000:1000
ENTRYPOINT ["python", "-u", "/app/enricher.py"]
