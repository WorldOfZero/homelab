# Render the collection posters (posters/README.md) at build time, so every deploy uploads the
# current designs. An image made by hand in collection-images/ wins over its rendered poster.
FROM python:3.13-slim AS posters
WORKDIR /src
COPY posters/requirements.txt posters/
RUN pip install --no-cache-dir -r posters/requirements.txt
COPY auto-collections.json ./
COPY posters/ posters/
COPY collection-images/ collection-images/
# The logos aren't kept in git (posters/logos/sources.yaml); download them from Wikimedia.
RUN python posters/fetch_logos.py
RUN python posters/make_posters.py --all --keep collection-images --out collection-images

FROM python:3.13-slim

# tzdata so RUN_AT is interpreted in the container's TZ
RUN pip install --no-cache-dir pyyaml==6.0.2 tzdata==2025.2

WORKDIR /app
COPY enricher.py config.yaml auto-collections.json ./
COPY --from=posters /src/collection-images/ ./collection-images/

USER 1000:1000
ENTRYPOINT ["python", "-u", "/app/enricher.py"]
