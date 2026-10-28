# Production Flask & MongoDB Microservice on Kubernetes (Minikube) & Docker

A production-ready implementation of a Python Flask REST API connected to an authenticated MongoDB database, containerized with Docker, orchestrated with Docker Compose, and deployed on Kubernetes (Minikube) with autoscaling (HPA), persistent storage, and secure networking.

---

## 📋 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Project Structure](#-project-structure)
3. [CLI Authentication Setup](#-cli-authentication-setup)
   - [Docker Hub CLI Authentication (`shivanshdwivedi222`)](#1-docker-hub-cli-authentication)
   - [GitHub CLI / Git Authentication (`shivanshdwivedi978`)](#2-github--git-cli-authentication)
4. [Building and Pushing the Docker Image](#-building-and-pushing-the-docker-image)
5. [Local Deployment with Docker Compose](#-local-deployment-with-docker-compose)
6. [Kubernetes Deployment on Minikube](#-kubernetes-deployment-on-minikube)
   - [Prerequisites & Minikube Setup](#1-prerequisites--minikube-setup)
   - [Deploying All Kubernetes Manifests](#2-deploying-all-kubernetes-manifests)
   - [Accessing the Application](#3-accessing-the-application)
7. [Testing & Verification](#-testing--verification)
   - [Automated API Testing](#1-automated-api-testing)
   - [HPA Autoscaling Simulation (High-Traffic Test)](#2-hpa-autoscaling-simulation-high-traffic-test)
   - [Database Persistence Verification](#3-database-persistence-verification)
8. [Technical Deep Dives](#-technical-deep-dives)
   - [DNS Resolution in Kubernetes for Inter-Pod Communication](#1-dns-resolution-in-kubernetes)
   - [Resource Requests and Limits in Kubernetes](#2-resource-requests-and-limits)
   - [StatefulSet vs Deployment for Databases](#3-statefulset-vs-deployment-for-databases)
9. [Design Choices & Alternatives Considered](#-design-choices--alternatives-considered)

---

## 🏛 Architecture Overview

```mermaid
graph TD
    Client([External Client / Browser]) -->|HTTP Port 30005| FlaskSvc[Kubernetes NodePort Service: flask-service]
    
    subgraph Kubernetes Cluster / Minikube
        FlaskSvc --> FlaskPod1[Flask Pod 1]
        FlaskSvc --> FlaskPod2[Flask Pod 2]
        FlaskSvc -.-> FlaskPodN[Flask Pod 3-5 Autoscaled by HPA]
        
        HPA[Horizontal Pod Autoscaler<br/>Target: >70% CPU<br/>Min: 2, Max: 5] -.->|Monitors Metrics| FlaskPod1
        HPA -.->|Monitors Metrics| FlaskPod2

        FlaskPod1 -->|mongodb-service:27017<br/>Authenticated via Secret| MongoSvc[Internal ClusterIP Service: mongodb-service]
        FlaskPod2 -->|mongodb-service:27017<br/>Authenticated via Secret| MongoSvc

        MongoSvc --> MongoPod[(MongoDB StatefulSet Pod: mongodb-0<br/>Auth: admin / password123)]
        MongoPod --> PVC[Persistent Volume Claim: mongo-pvc]
        PVC --> PV[Persistent Volume: mongo-pv<br/>Mount: /data/db]
    end
```

### Application Specifications
- **Framework**: Python 3.9 + Flask 2.0.2 + PyMongo 3.12.0
- **Database**: MongoDB 6.0 with Root Authentication enabled (`admin` / `password123`)
- **Container Registry**: Docker Hub (`shivanshdwivedi222/flask-mongodb-app:latest`)
- **High Availability**: 2 replicas minimum, autoscaling up to 5 replicas via HPA at >70% CPU
- **Security**: Non-root container execution (UID 10001), Kubernetes Secrets for credentials, private ClusterIP for database

---

## 📁 Project Structure

```text
.
├── Dockerfile                  # Secure, lightweight non-root multi-arch container image
├── docker-compose.yml          # Multi-container orchestration (Flask + Auth MongoDB)
├── requirements.txt            # Pinned dependencies (Flask, Werkzeug, PyMongo)
├── app.py                      # Flask REST API with authentication & health checks
├── .dockerignore               # Optimizes Docker build context
├── .env.example                # Template for environment variables
├── test_api.sh                 # Automated endpoint testing script
├── load_test_hpa.sh            # High-concurrency traffic simulator for HPA validation
├── k8s/                        # Kubernetes Resource Manifests
│   ├── kustomization.yaml      # Declarative batch deployment file
│   ├── mongo-secret.yaml       # Sensitive database credentials & connection URI
│   ├── mongo-configmap.yaml    # Database hostname, port, and configuration
│   ├── mongo-pv.yaml           # Persistent Volume (1Gi storage)
│   ├── mongo-pvc.yaml          # Persistent Volume Claim for MongoDB
│   ├── mongo-service.yaml      # ClusterIP Service (internal-only database access)
│   ├── mongo-statefulset.yaml  # StatefulSet for MongoDB with persistent storage
│   ├── flask-deployment.yaml   # Deployment with 2 replicas, resource limits & probes
│   ├── flask-service.yaml      # NodePort Service exposing Flask on port 30005
│   └── flask-hpa.yaml          # Horizontal Pod Autoscaler (2 to 5 pods @ 70% CPU)
└── README.md                   # Complete documentation and run guide
```

---

## 🔑 CLI Authentication Setup

### 1. Docker Hub CLI Authentication
**Docker Username:** `shivanshdwivedi222`

Docker Hub no longer recommends plain passwords over the CLI. Use a Personal Access Token (PAT):

1. **Generate a Docker Hub Token**:
   - Log in to [hub.docker.com](https://hub.docker.com).
   - Click on your avatar in the top right -> **Account Settings** -> **Security** -> **New Access Token**.
   - Set description: `cli-access` with **Read, Write, Delete** permissions.
   - Copy the generated token (`dckr_pat_...`).

2. **Authenticate from your Terminal**:
   ```bash
   docker login -u shivanshdwivedi222
   # When prompted for Password, paste your Docker Personal Access Token
   ```
   **Verification:** You should see `Login Succeeded`.

---

### 2. GitHub / Git CLI Authentication
**GitHub Username:** `shivanshdwivedi978`  
**Email:** `shivanshdwivedi978@gmail.com`

#### Step A: Configure Git Identity
Set your local repository author details:
```bash
git config --global user.name "shivanshdwivedi978"
git config --global user.email "shivanshdwivedi978@gmail.com"
```

#### Step B: Authenticate via GitHub CLI (`gh`) - Recommended
If you have `gh` installed:
```bash
brew install gh   # If not already installed
gh auth login
```
Follow the interactive prompts:
- What account do you want to log into? -> **GitHub.com**
- What is your preferred protocol for Git operations? -> **HTTPS**
- Authenticate Git with your GitHub credentials? -> **Yes**
- How would you like to authenticate? -> **Login with a web browser** (or paste your GitHub token).

#### Step C: Alternative - Authenticate via SSH Key
1. Generate an SSH key:
   ```bash
   ssh-keygen -t ed25519 -C "shivanshdwivedi978@gmail.com" -f ~/.ssh/id_ed25519_github -N ""
   ```
2. Start the ssh-agent and add your key:
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519_github
   ```
3. Copy the public key to clipboard:
   ```bash
   pbcopy < ~/.ssh/id_ed25519_github.pub
   ```
4. Add it to GitHub:
   - Go to [github.com/settings/keys](https://github.com/settings/keys) -> **New SSH Key**.
   - Paste the key and click **Add SSH key**.
5. Test your connection:
   ```bash
   ssh -T git@github.com
   # Hi shivanshdwivedi978! You've successfully authenticated...
   ```

#### Step D: Commit and Push this Project
```bash
cd /Users/piyushshrivastava/shivansh
git add .
git commit -m "feat: complete flask mongodb application with docker and kubernetes setup"

# Create remote repository on GitHub (via gh CLI):
gh repo create flask-mongodb-k8s --public --source=. --remote=origin --push

# Or add manually if created on GitHub web:
# git remote add origin git@github.com:shivanshdwivedi978/flask-mongodb-k8s.git
# git branch -M main
# git push -u origin main
```

---

## 🐳 Building and Pushing the Docker Image

1. **Build the container image**:
   ```bash
   docker build -t shivanshdwivedi222/flask-mongodb-app:latest .
   ```

2. **Test the image locally (optional)**:
   ```bash
   docker run --rm -p 5000:5000 shivanshdwivedi222/flask-mongodb-app:latest
   ```

3. **Push to Docker Hub**:
   ```bash
   docker push shivanshdwivedi222/flask-mongodb-app:latest
   ```

---

## 🚀 Local Deployment with Docker Compose

Docker Compose runs MongoDB with root authentication and starts the Flask container on a shared bridge network.

### 1. Start the Stack
Make sure Docker Desktop is running, then execute:
```bash
docker compose up --build -d
```

### 2. Verify Container Health
```bash
docker compose ps
```
Both `mongodb` and `flask_app` should be in the `healthy` and `running` state:
```text
NAME         IMAGE                                      STATUS                    PORTS
flask_app    shivanshdwivedi222/flask-mongodb-app:latest   Up 20s (healthy)          0.0.0.0:5000->5000/tcp
mongodb      mongo:6.0                                  Up 20s (healthy)          0.0.0.0:27017->27017/tcp
```

### 3. Test the Endpoints
Run the automated test script:
```bash
./test_api.sh http://localhost:5000
```

### 4. Stop the Stack
```bash
# Stop containers but keep database volume:
docker compose down

# Or stop containers and remove volume:
docker compose down -v
```

---

## ☸️ Kubernetes Deployment on Minikube

### 1. Prerequisites & Minikube Setup

1. **Start Docker Desktop**:
   Open Docker Desktop from `/Applications/Docker.app` and wait until the Docker engine starts.

2. **Install & Start Minikube**:
   If not yet installed:
   ```bash
   brew install minikube
   ```
   Start Minikube using the Docker driver with adequate resources:
   ```bash
   minikube start --driver=docker --cpus=4 --memory=4096
   ```

3. **Enable the Metrics Server** (Required for HPA autoscaling):
   ```bash
   minikube addons enable metrics-server
   ```
   Verify metrics-server:
   ```bash
   kubectl get pods -n kube-system -l k8s-app=metrics-server
   ```

---

### 2. Deploying All Kubernetes Manifests

Deploy all manifests in one command using Kustomize:
```bash
kubectl apply -k k8s/
```
*(Or individually: `kubectl apply -f k8s/`)*

#### Execution Order if applying individually:
1. `kubectl apply -f k8s/mongo-secret.yaml`
2. `kubectl apply -f k8s/mongo-configmap.yaml`
3. `kubectl apply -f k8s/mongo-pv.yaml`
4. `kubectl apply -f k8s/mongo-pvc.yaml`
5. `kubectl apply -f k8s/mongo-service.yaml`
6. `kubectl apply -f k8s/mongo-statefulset.yaml`
7. `kubectl apply -f k8s/flask-deployment.yaml`
8. `kubectl apply -f k8s/flask-service.yaml`
9. `kubectl apply -f k8s/flask-hpa.yaml`

#### Verify Deployment Status:
```bash
kubectl get all
kubectl get pvc,pv
kubectl get hpa
```

Expected Pods status:
```text
NAME                             READY   STATUS    RESTARTS   AGE
pod/flask-app-79848bc449-abc12   1/1     Running   0          45s
pod/flask-app-79848bc449-xyz34   1/1     Running   0          45s
pod/mongodb-0                    1/1     Running   0          60s
```

---

### 3. Accessing the Application

In Minikube, the `flask-service` is exposed as a `NodePort` on port `30005`.

#### Option A: Minikube Service URL (Direct Browser Access)
Run:
```bash
minikube service flask-service --url
```
This prints the exact localhost or node URL (e.g., `http://127.0.0.1:51234` or `http://192.168.49.2:30005`).

#### Option B: Port Forwarding (Direct localhost:5000 access)
```bash
kubectl port-forward svc/flask-service 5000:5000
```
The application is now accessible directly at `http://localhost:5000`.

---

## 🧪 Testing & Verification

### 1. Automated API Testing
Run the included test script against your running Minikube service or port-forward URL:
```bash
# If port-forwarding to 5000:
./test_api.sh http://localhost:5000

# Or with Minikube Service URL:
./test_api.sh $(minikube service flask-service --url)
```

#### Manual `curl` Verification Commands:

1. **Root Endpoint (`/`)**:
   ```bash
   curl http://localhost:5000/
   ```
   **Output:**
   ```text
   Welcome to the Flask app! The current time is: 2026-10-28 21:30:15.123456
   ```

2. **Health Check (`/healthz`)**:
   ```bash
   curl -i http://localhost:5000/healthz
   ```
   **Output:**
   ```json
   HTTP/1.1 200 OK
   {"database":"connected","status":"healthy","timestamp":"2026-10-28T16:00:15.000000"}
   ```

3. **Insert Data (`POST /data`)**:
   ```bash
   curl -X POST http://localhost:5000/data \
     -H "Content-Type: application/json" \
     -d '{"candidate": "Shivansh Dwivedi", "task": "Kubernetes Deployment"}'
   ```
   **Output:**
   ```json
   {"status": "Data inserted"}
   ```

4. **Retrieve Data (`GET /data`)**:
   ```bash
   curl http://localhost:5000/data
   ```
   **Output:**
   ```json
   [{"candidate":"Shivansh Dwivedi","task":"Kubernetes Deployment"}]
   ```

---

### 2. HPA Autoscaling Simulation (High-Traffic Test)

The Horizontal Pod Autoscaler (HPA) monitors CPU utilization of the Flask pods and scales them from **2 replicas up to 5 replicas** whenever average CPU utilization crosses **70%**.

1. **In Terminal 1: Watch the HPA and Pods**:
   ```bash
   kubectl get hpa flask-hpa --watch
   ```
   *(In another window: `kubectl get pods -l app=flask-app --watch`)*

2. **In Terminal 2: Run the High-Traffic Generator**:
   ```bash
   ./load_test_hpa.sh http://localhost:5000 120
   ```
   *This launches 20 concurrent workers issuing continuous GET and POST requests.*

3. **Observed Autoscaling Behavior**:
   - Initial state: `2/2` replicas, CPU at `1% / 70%`.
   - Under load: CPU rises to `95% / 70%`.
   - HPA scales pods from `2` -> `3` -> `5` replicas.
   - After load finishes: CPU drops to `<5%`, and HPA scales back down to `2` replicas following the standard cooldown window.

---

### 3. Database Persistence Verification

To verify data persists even if the database pod crashes or restarts:
1. Insert test data via `curl -X POST http://localhost:5000/data -H "Content-Type: application/json" -d '{"persistent":"record-1"}'`.
2. Delete the MongoDB pod:
   ```bash
   kubectl delete pod mongodb-0
   ```
3. Kubernetes StatefulSet will automatically recreate `mongodb-0` and remount the Persistent Volume Claim `mongo-pvc`.
4. Once `mongodb-0` is Running, query the data again:
   ```bash
   curl http://localhost:5000/data
   ```
   **Result:** All previously inserted documents remain completely intact!

---

## 🔬 Technical Deep Dives

### 1. DNS Resolution in Kubernetes
#### How DNS Resolution Works in Kubernetes:
1. **CoreDNS**: Kubernetes deploys a cluster-wide DNS server (`coredns` in the `kube-system` namespace).
2. **Kubelet `/etc/resolv.conf` Injection**: When a pod starts, `kubelet` automatically configures its `/etc/resolv.conf` file with the cluster DNS server's ClusterIP and search domains:
   ```text
   nameserver 10.96.0.10
   search default.svc.cluster.local svc.cluster.local cluster.local
   options ndots:5
   ```
3. **FQDN Resolution**:
   - When the Flask pod connects to `mongodb-service:27017`, the resolver appends the search domains to form the Fully Qualified Domain Name (FQDN):  
     `mongodb-service.default.svc.cluster.local`
   - CoreDNS resolves this FQDN to the internal ClusterIP assigned to the MongoDB service.
   - Kube-proxy (via iptables or IPVS rules) routes the traffic directly to the backend MongoDB pod IP.

#### Connecting Flask to MongoDB:
- The Flask app connects via the connection string:
  `mongodb://admin:password123@mongodb-service:27017/flask_db?authSource=admin`
- Because both services reside in the same namespace (`default`), `mongodb-service` is sufficient. If deployed across namespaces, the cross-namespace DNS name `mongodb-service.<namespace>.svc.cluster.local` is used.

---

### 2. Resource Requests and Limits
Resource management ensures cluster stability, predictable scheduling, and fair resource allocation.

#### Configuration in Manifests:
- **Requests**: `cpu: "200m"` (0.2 CPU core), `memory: "250Mi"`
- **Limits**: `cpu: "500m"` (0.5 CPU core), `memory: "500Mi"`

#### Use Cases and Importance:
1. **Resource Requests (Scheduling Guarantee)**:
   - The Kubernetes scheduler (`kube-scheduler`) uses `requests` to decide which worker node has sufficient unallocated capacity to place the pod.
   - If a node does not have at least `200m` CPU and `250Mi` RAM available, the pod will not be scheduled there.
2. **Resource Limits (Container Enforcement)**:
   - Limits are enforced at the Linux kernel level via **cgroups**.
   - **CPU Throttling**: CPU is a compressible resource. If a pod exceeds `500m` (50% of one core), the Linux CFS scheduler throttles the pod's CPU cycles instead of killing it.
   - **OOMKilled (Out of Memory)**: Memory is non-compressible. If a pod attempts to allocate more than `500Mi` RAM, the kernel OOM killer terminates the container with exit code 137, preventing memory exhaustion from affecting other tenant pods.
3. **Quality of Service (QoS) Class**:
   - With both requests and limits configured where limits > requests, Kubernetes assigns the pod the **Burstable** QoS class. This allows the Flask app to burst up to 0.5 CPU during high load while maintaining baseline resource efficiency.

---

### 3. StatefulSet vs Deployment for Databases

| Feature | Deployment | StatefulSet (Selected) |
| :--- | :--- | :--- |
| **Pod Identity** | Ephemeral, random hash (`flask-app-79848bc449-abc12`) | Stable, unique network identity (`mongodb-0`) |
| **Storage Binding** | Pods share volume or recreate volume on reschedule | Dedicated PV/PVC per ordinal index (`mongo-pvc`) |
| **Startup / Shutdown Order** | Random, concurrent | Strict ordered startup (`0, 1, ...`) and graceful teardown |
| **Headless DNS Support** | Service load-balances across pods | Pod-specific DNS records (`mongodb-0.mongodb-service`) |

**Why StatefulSet was chosen for MongoDB:**  
Databases require stable hostnames, deterministic startup sequences, and permanent binding to their persistent volumes to avoid data corruption across pod restarts and rescheduling.

---

## 💡 Design Choices & Alternatives Considered

1. **StatefulSet for MongoDB vs Single Pod / Deployment**:
   - *Choice*: StatefulSet with PersistentVolumeClaim.
   - *Alternative Considered*: A standard Deployment.
   - *Rationale*: A Deployment does not guarantee stable network identity or deterministic volume binding upon node failures, risking split-brain or volume attachment locks.

2. **Service Types (NodePort vs LoadBalancer vs Ingress)**:
   - *Choice*: `NodePort` for the Flask application and `ClusterIP` for MongoDB.
   - *Alternative Considered*: Ingress Controller or LoadBalancer.
   - *Rationale*: NodePort works reliably out-of-the-box in all local environments (Minikube, kind, k3s) without requiring external cloud providers, metallb, or ingress controller setups. For MongoDB, `ClusterIP` strictly guarantees the database port is never exposed to the external internet.

3. **Kubernetes Secret vs ConfigMap for Credentials**:
   - *Choice*: Base64/stringData `Secret` for username, password, and full connection URI; `ConfigMap` for non-sensitive ports and hostnames.
   - *Rationale*: Prevents leaking database credentials in plain-text git repositories and supports RBAC policies restricting secret access to privileged users.

4. **Multi-Stage / Non-Root Docker Image**:
   - *Choice*: `python:3.9-slim` running as non-root user `appuser` (UID 10001).
   - *Alternative Considered*: Standard `python:3.9` running as `root`.
   - *Rationale*: Running as root inside containers is a major security risk. The slim image minimizes image size (reducing pull times and attack surface) while adhering to Kubernetes Pod Security Standards.

5. **Liveness and Readiness Probes**:
   - *Choice*: HTTP `/healthz` for Flask (which pings MongoDB) and `mongosh --eval "db.adminCommand('ping')"` for MongoDB.
   - *Rationale*: Ensures Kubernetes does not route traffic to Flask until it is ready and connected to the database, preventing `502 Bad Gateway` errors during rolling deployments.
