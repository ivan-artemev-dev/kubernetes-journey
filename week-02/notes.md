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

Week 02 — Part 2: GDELT Dashboard

What We Did

We dockerized the GDELT Analytics Dashboard — a web interface that displays data collected by the parser. The dashboard consists of a FastAPI backend that queries Elasticsearch, and an nginx-served React frontend that proxies API requests to the backend. We wrote Dockerfiles for both services and added them to the existing docker-compose.yml alongside the pipeline and Elasticsearch.

Key Concepts

Multi-stage build (frontend)
Node.js is only needed to build static files. In the final image it's not needed — only nginx and the dist/ folder remain. This reduces image size from ~1GB to ~50MB.

depends_on
Guarantees that a container is started, but not that the app inside is ready. Elasticsearch needs extra time to initialize after the container starts.

Container networking
Containers are isolated — they cannot reach localhost of the host machine. They communicate with each other by service name (e.g. elasticsearch, gdelt-backend). Docker resolves service names to IPs automatically within its internal network.

## Stage 2 — Kubernetes Manifests

**What We Did**

Wrote Kubernetes manifests for all four services and deployed them to minikube.

**Elasticsearch**
- `StatefulSet` instead of Deployment — because data must survive pod restarts
- `PersistentVolumeClaim` (150Gi) — reserves disk storage separately from the pod
- `Service` (ClusterIP) — accessible only inside the cluster by name

**Pipeline**
- `Deployment` only — no Service needed, pipeline only writes to Elasticsearch, nothing calls it

**Backend**
- `Deployment` + `Service` (ClusterIP) — accessible inside cluster by other pods

**Frontend**
- `Deployment` + `Service` (ClusterIP) + `Ingress`
- Ingress routes: `/api/*` → backend, `/*` → frontend
- Added `gdelt.local` to Windows hosts file to resolve the domain locally

**Result:** All pods Running, dashboard accessible at `http://gdelt.local`