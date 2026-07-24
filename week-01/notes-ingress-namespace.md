## Ingress — Permanent External Access

### What is Ingress

Ingress is a reverse proxy inside the cluster. It's the permanent solution for external access, unlike `port-forward` which is just a temporary developer tool.

Analogy:
```
Without Kubernetes:
Browser → nginx/caddy (reverse proxy) → FastAPI backend

In Kubernetes:
Browser → Ingress → Service → Pod
```

### What Ingress can do
- Route by domain: `api.mysite.com` → backend, `mysite.com` → frontend
- Route by path: `/api/*` → backend, `/*` → frontend
- Terminate SSL (HTTPS)

### For GDELT project (future):
```
Browser
├── /api/* → Service → Pod (FastAPI backend)
└── /*     → Service → Pod (React frontend)
```

### Ingress manifest

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-first-ingress
spec:
  rules:
  - host: my-nginx.local       # domain name
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-first-service   # which Service to route to
            port:
              number: 80
```

### Enable Ingress in minikube

```bash
minikube addons enable ingress

# Check ingress controller is running
kubectl get pods -n ingress-nginx
```

### Important: minikube network limitation

minikube runs inside a Docker container with its own internal network (`192.168.49.2`). Windows/external machines can't reach it directly.

Workaround for development — port-forward to Ingress controller:
```bash
kubectl port-forward --address 0.0.0.0 -n ingress-nginx service/ingress-nginx-controller 8080:80
```

In a real cluster on real machines — Ingress controller sits directly on the node's IP, no port-forward needed.

### Why port 80 requires sudo

Ports below 1024 are reserved for root in Linux. Solution: use port 8080 (or any port above 1024) in port-forward.

### Full request chain

```
Browser (my-nginx.local:8080)
    ↓ hosts file → 192.168.35.100:8080
Linux machine (port-forward)
    ↓
Ingress (routes my-nginx.local → my-first-service)
    ↓
Service (finds pods by label: app: nginx)
    ↓
Pod (nginx container)
```

### Windows hosts file

To use a custom domain locally, add it to `C:\Windows\System32\drivers\etc\hosts`:
```
192.168.35.100  my-nginx.local
```

---

## Namespace — Isolation Inside the Cluster

### What is Namespace

Folders inside a Kubernetes cluster. Isolate objects from each other.

### Default namespaces

```bash
kubectl get namespaces
```

| Namespace | Purpose |
|---|---|
| `default` | Where objects go if no namespace specified |
| `kube-system` | Kubernetes internal components (etcd, apiserver...) |
| `ingress-nginx` | Ingress controller lives here |
| `kube-public` | Public cluster info, rarely used |
| `kube-node-lease` | Node heartbeats, internal use |

### When to use namespaces

**Multiple projects on one cluster:**
```
namespace: project-a
namespace: project-b
```

**One project, separate infrastructure:**
```
namespace: gdelt        → parser, backend, frontend
namespace: monitoring   → Prometheus + Grafana
namespace: logging      → ELK stack
```

### How to specify namespace in a manifest

```yaml
metadata:
  name: my-first-deployment
  namespace: gdelt        # add this line
```

### Important: kubectl apply behavior

`kubectl apply` only touches what's in the file. It does NOT delete objects in other namespaces. To delete old objects — do it manually.

```bash
kubectl delete deployment my-first-deployment -n default
```

### Commands

```bash
# Create namespace
kubectl create namespace gdelt

# List all namespaces
kubectl get namespaces

# Get all objects in a namespace
kubectl get all -n gdelt

# Get all objects in default namespace
kubectl get all
```

### ReplicaSet — bonus discovery today

We never created ReplicaSet manually — Deployment creates it automatically.

```
Deployment (you create)
    ↓ auto-creates
ReplicaSet (watches replica count)
    ↓ auto-creates
Pod (running container)
```

Never create ReplicaSet directly — always use Deployment. Deployment also supports rollback, ReplicaSet does not.

## Next Steps
- [ ] Write Dockerfile for parse_gdelt
- [ ] Deploy first real service to gdelt namespace
- [ ] Learn ConfigMap and Secrets
