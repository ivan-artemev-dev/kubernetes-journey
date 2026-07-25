# Kubernetes Journey 🚀

Learning Kubernetes by deploying a real project — step by step, from a single machine to a full cluster.

## About This Repository

This is my hands-on Kubernetes learning path. Instead of toy examples, I'm containerizing and deploying a real project I built: a **GDELT Analytics / OSINT Dashboard** — a system that collects and analyzes global news events from the [GDELT](https://www.gdeltproject.org/) open database.

The goal is to go through every stage properly — understanding why, not just how.

## The Project Being Deployed

**GDELT Analytics Platform** — an OSINT dashboard for monitoring mentions of specific entities (persons, organizations, countries) in world media.

### Architecture
| Service | Stack | Description |
|---|---|---|
| `parse_gdelt` | Python, cron | Downloads GDELT GKG v2 files every 15 min, parses and indexes into Elasticsearch |
| `gdelt-dashboard` backend | FastAPI + Elasticsearch | REST API: feed, search, trends, entity analytics, geo, GCAM metrics |
| `gdelt-dashboard` frontend | React + Vite | Pages: Feed, Search, Entity, Trends, Map, Historical analysis |
| Storage | Elasticsearch | Main index `gdelt_gkg`, SQLite for reference data |

Currently running on a **single machine without containers**. The journey is to properly migrate this to Kubernetes.

## Learning Path

### Stage 1 — Containerization ✅
- [x] Dockerfile for `parse_gdelt`
- [x] Dockerfile for `gdelt-dashboard` backend
- [x] Dockerfile for `gdelt-dashboard` frontend
- [x] docker-compose to run everything locally
- [x] Push images to local registry (minikube)

### Stage 2 — Kubernetes Locally (minikube) ✅
- [x] Namespace, PVC, StatefulSet for Elasticsearch
- [x] Deployments for all services
- [x] Services (ClusterIP)
- [x] Ingress with routing rules
- [x] Dashboard running at gdelt.local

### Stage 3 — CI/CD (next)
- [ ] GitHub Actions pipeline
- [ ] Auto build and push images to registry
- [ ] Auto deploy to Kubernetes on git push

### Stage 4 — Production Practices
- [ ] ConfigMaps and Secrets
- [ ] Liveness and readiness probes
- [ ] Resource limits and requests
- [ ] Helm chart
      
## Repository Structure

```
kubernetes-journey/
├── week-01/
│   ├── notes.md        # Theory: core concepts
│   └── manifests/      # First yaml files
├── week-02/
│   └── ...
├── project/
│   ├── docker/         # Dockerfiles
│   └── k8s/            # Kubernetes manifests
└── resources.md        # Useful links and references
```

## Progress Log
| Week | Topic | Status |
|---|---|---|
| Week 1 | Core concepts, first manifests | ✅ Done |
| Week 2 | Docker, docker-compose, Kubernetes manifests | ✅ Done |

## Stack & Tools

![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-005571?style=flat&logo=elasticsearch&logoColor=white)

---

*Learning in public — every problem, every fix, every lesson documented here.*
