# Week 01 — Core Concepts & First Steps

## What is Kubernetes and why do I need it

My GDELT service runs on a single machine — parser, backend, frontend, Elasticsearch all started manually. If the machine goes down, everything goes down. If the parser crashes at night, nobody restarts it.

Kubernetes solves exactly this:
- **Self-healing** — if a pod crashes, K8s restarts it automatically
- **Scaling** — need 2 copies of the backend? One line change
- **Declarative** — you describe what you want, K8s figures out how to make it happen

## Key Concepts

### Cluster
A group of machines that Kubernetes manages as one. You say "run my parser" — K8s decides where.

### Node
One machine in the cluster. Can be:
- **Control plane** (master) — manages the cluster
- **Worker** — runs your applications

In minikube, one node does both roles.

### Pod
The smallest unit in Kubernetes. A wrapper around one (or more) containers. Each service in my project will be a separate Pod:

```
Node (minikube)
├── Pod: parse_gdelt      → parser container
├── Pod: backend          → FastAPI container
├── Pod: frontend         → React container
└── Pod: elasticsearch    → ES container
```

Important: **Pod names change every time they are recreated.** Never rely on a pod name for communication.

### Deployment
Tells Kubernetes: "I want this pod to always be running with N replicas. If it crashes — restart it."

This is the right way to run pods. Never use `kubectl run` in practice — always use a Deployment manifest.

### Service
Gives a stable address to a set of pods. Since pod names and IPs change on every restart, Service is the only reliable way to reach a pod.

### Namespace
Folders inside a cluster. Example: `production`, `staging`, `monitoring`.

## Kubernetes Internal Components

Visible via `kubectl get pods -n kube-system`:

| Component | Role |
|---|---|
| `kube-apiserver` | Entry point for all kubectl commands |
| `etcd` | Database of the entire cluster state |
| `kube-scheduler` | Decides which node to place a new pod on |
| `kube-controller-manager` | Watches state — ensures replicas count is always correct |
| `kube-proxy` | Network rules — routes traffic to the right pod |
| `coredns` | DNS inside the cluster — pods talk to each other by name |
| `storage-provisioner` | Creates persistent storage when requested |

## Commands Learned

```bash
# Check cluster node
kubectl get nodes

# See system pods
kubectl get pods -n kube-system

# See pods in default namespace
kubectl get pods

# Go inside a pod
kubectl exec -it <pod-name> -- /bin/bash

# Apply a manifest
kubectl apply -f my-deployment.yaml

# Delete a pod (Deployment will recreate it)
kubectl delete pod <pod-name>
```

## First Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-first-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
```

## Key Insight Today

Deleting a pod created by `kubectl run` — it's gone forever.  
Deleting a pod created by a Deployment — Kubernetes immediately creates a new one with a new name.

This is the fundamental difference. **Always use Deployments.**

## Difference from Docker Compose

| Docker Compose | Kubernetes |
|---|---|
| `restart: unless-stopped` | Deployment with replicas |
| All services in one file | Each service is a separate manifest |
| Single machine | Multiple machines (nodes) |
| You manage restarts | K8s manages everything |

## Next Steps
- [ ] Learn what Service is and create one
- [ ] Expose the nginx deployment outside the cluster
- [ ] Write first Dockerfile for parse_gdelt

## Service — Stable Access to Pods

### Why Service exists

Pod names and IPs change every time a pod is recreated. You can never rely on a pod's IP directly. Service solves this — it gives a stable endpoint that always points to the right pods, regardless of how many times they've been recreated.

### How Service finds Pods — Labels

Service doesn't connect to pods by name. It uses **labels** — key/value tags on pods.

In the Deployment manifest:
```yaml
labels:
  app: nginx
```

In the Service manifest:
```yaml
selector:
  app: nginx
```

Service finds all pods with matching label and routes traffic to them. This is why pod names can change freely — the label stays the same.

### Service types

| Type | When to use |
|---|---|
| `ClusterIP` | Default. Only accessible inside the cluster. Used for pod-to-pod communication (e.g. backend → elasticsearch) |
| `NodePort` | Opens a port on the node. Accessible from outside the cluster. Used for development. |
| `LoadBalancer` | Cloud only. Creates an external load balancer. Used in production. |

### First Service manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-first-service
spec:
  selector:
    app: nginx        # finds pods with this label
  type: NodePort
  ports:
  - port: 80          # port inside the cluster
    targetPort: 80    # port on the container
    nodePort: 30080   # port exposed on the node (outside)
```

### port-forward — developer tool

`kubectl port-forward` is NOT part of Kubernetes configuration. It's a temporary tunnel for development and debugging. Requires terminal to stay open.

```bash
# Forward with access from all network interfaces
kubectl port-forward service/my-first-service --address 0.0.0.0 8080:80
```

```
Windows browser → 192.168.35.100:8080 → port-forward → Service → Pod → nginx
```

In production this is replaced by **Ingress** — a permanent solution that's part of the cluster config.

### Key insight

`port-forward` listens on `127.0.0.1` (localhost) by default. To make it accessible from another machine, always add `--address 0.0.0.0`.

### Commands learned

```bash
# Apply service manifest
kubectl apply -f my-first-service.yaml

# Get minikube node IP
minikube ip

# Get service URL
minikube service my-first-service --url

# Port forward (temporary, for development)
kubectl port-forward service/my-first-service --address 0.0.0.0 8080:80

# List all services
kubectl get services
```

## Next Steps
- [ ] Learn Ingress — permanent external access solution
- [ ] Write Dockerfile for parse_gdelt
- [ ] Understand ClusterIP — how pods talk to each other inside the cluster
