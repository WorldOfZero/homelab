# Standard library only: no packages to install.
FROM python:3.13-slim

WORKDIR /app
COPY shopping_sync.py ./

USER 1000:1000
ENTRYPOINT ["python", "-u", "/app/shopping_sync.py"]
