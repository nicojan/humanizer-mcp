FROM python:3.12-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY src/ ./src/
COPY data/ ./data-defaults/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Pre-create /app/data with the runtime user's ownership so that when
# Docker mounts a fresh named volume at this path, the volume-populate
# step carries over the directory's UID/GID/mode. Without this line,
# a fresh volume's root dir is owned root:root mode 755 and the non-root
# container user (1026:100) cannot write to it, so the entrypoint's
# first-run clone fails with "Permission denied" and the container goes
# into a restart loop.
RUN mkdir -p /app/data && chown 1026:100 /app/data

# CRITICAL: Set PYTHONPATH so 'from src.xxx import yyy' resolves correctly.
# Without this, Python adds /app/src/ to the path (the script's directory),
# not /app/, causing ModuleNotFoundError on all src.* imports.
ENV PYTHONPATH=/app
ENV GIT_AUTHOR_NAME=mcp-humanizer
ENV GIT_AUTHOR_EMAIL=mcp-humanizer@human.local

USER 1026:100

EXPOSE 8016

ENTRYPOINT ["./entrypoint.sh"]
