# Week 02 — Docker & docker-compose

## What We Did
- Wrote a `Dockerfile` for `parse_gdelt` based on `python:3.11-slim`
- Launched two containers via `docker-compose`: Elasticsearch + gdelt-pipeline
- Verified that the pipeline downloads GDELT files and indexes them into Elasticsearch

## Key Concepts

**Image vs Container**
- Image — immutable template built from a Dockerfile
- Container — a running instance of an image

**localhost inside a container**
- `localhost` = the container itself, not the host machine
- Containers communicate by service name: `http://elasticsearch:9200`
- Docker resolves the name to an IP inside its internal network

**Environment variables**
- Never hardcode config — pass it via `ENV` or `-e` flags
- Same image works in any environment (dev, staging, prod)

**depends_on**
- Guarantees the container is started
- Does NOT guarantee the app inside is ready to accept connections

## Next Step
Translate docker-compose into Kubernetes manifests
