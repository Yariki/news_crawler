# Kubernetes & Helm — Concepts and File Reference

A self-contained guide to every concept and file used in this project's Kubernetes deployment.
All template files live under `k8s/news-crawler/templates/`.

---

## Table of Contents

1. [Kubernetes in one paragraph](#1-kubernetes-in-one-paragraph)
2. [What is Helm?](#2-what-is-helm)
3. [Chart.yaml](#3-chartyaml)
4. [The `kind` field — Kubernetes resource types](#4-the-kind-field--kubernetes-resource-types)
5. [The `type` field — subtypes on specific resources](#5-the-type-field--subtypes-on-specific-resources)
6. [Template files — one by one](#6-template-files--one-by-one)
   - [_helpers.tpl](#_helperstpl)
   - [ConfigMap](#configmap)
   - [Secret](#secret)
   - [Deployment](#deployment)
   - [Service](#service)
   - [PersistentVolumeClaim (PVC)](#persistentvolumeclaim-pvc)
   - [Ingress](#ingress)

---

## 1. Kubernetes in one paragraph

Kubernetes (K8s) is a container orchestration platform. You describe the **desired state** of your system — how many copies of each container should run, how they communicate, how much storage they need — and Kubernetes continuously reconciles the cluster toward that state. You never say "run this command"; you declare "I want 2 replicas of the backend image behind a service on port 8000" and Kubernetes makes it happen and keeps it that way.

Every resource in Kubernetes is described by a **YAML manifest**. Each manifest has four top-level fields:

```yaml
apiVersion: apps/v1   # which Kubernetes API group and version handles this
kind: Deployment      # what type of resource this is
metadata:             # name, namespace, labels
spec:                 # the actual configuration
```

---

## 2. What is Helm?

Helm is a **package manager for Kubernetes**. Without Helm, you manage raw YAML files. That becomes painful the moment you have more than one environment (dev/test/prod), because the only difference between environments is a handful of values — the database password, the ingress hostname, the number of replicas — and you would have to maintain three near-identical copies of every file.

Helm solves this with **templates and values**:

- Templates are regular Kubernetes YAML files with `{{ }}` placeholders.
- Values are the data that fills in those placeholders, supplied from `values.yaml` files.
- Helm renders the templates + values into complete YAML and sends the result to Kubernetes.

### Key concepts

| Term | Meaning |
|------|---------|
| **Chart** | A Helm package — a directory containing templates, values, and metadata |
| **Release** | A deployed instance of a chart. You can install the same chart multiple times under different release names |
| **Values file** | A YAML file (`values.yaml`, `values.prod.yaml`, …) that provides data to templates |
| **Template** | A `.yaml` file under `templates/` that uses Go template syntax (`{{ .Values.xxx }}`) |
| **`helm upgrade --install`** | Deploy the chart if not installed yet, or update it if already running |

### How values are merged

Multiple values files can be layered. Helm applies them left to right; later files override earlier ones:

```bash
helm upgrade --install my-release ./news-crawler \
  -f values.yaml \          # base defaults
  -f values.prod.yaml \     # production overrides
  --set-string backend.image.tag=abc123   # CI-level overrides (highest priority)
```

### Template syntax cheat-sheet

```
{{ .Values.backend.replicaCount }}   inject a value
{{ include "news-crawler.fullname" . }}  call a named template from _helpers.tpl
{{- if .Values.postgres.enabled }}   conditional block
{{- end }}
{{ .Release.Name }}   built-in: the release name provided at install time
{{ .Release.Namespace }}   built-in: the target namespace
```

---

## 3. Chart.yaml

**File:** `k8s/news-crawler/Chart.yaml`

```yaml
apiVersion: v2
name: news-crawler
description: Helm chart for the news crawler stack on Kubernetes
type: application
version: 0.1.0
appVersion: 0.1.0
```

This is the **identity card** of the Helm chart. Helm reads it before doing anything else.

| Field | Meaning |
|-------|---------|
| `apiVersion: v2` | Helm 3 chart format. Always `v2` for modern charts |
| `name` | The chart's name. Becomes part of generated Kubernetes resource names |
| `description` | Human-readable summary |
| `type: application` | This chart deploys a runnable application. The other option is `library` (shared helpers only, not deployable) |
| `version` | The chart's own version. Bump this when you change the chart itself |
| `appVersion` | The version of the application the chart deploys. Informational only; the actual image tag comes from `values.yaml` |

---

## 4. The `kind` field — Kubernetes resource types

The `kind` field in every YAML manifest tells Kubernetes which object type to create or update. The following kinds are used in this chart:

### `Deployment`

**Files:** `backend-deployment.yaml`, `frontend-deployment.yaml`, `postgres-deployment.yaml`, `elasticsearch-deployment.yaml`, `kibana-deployment.yaml`

A Deployment manages a **set of identical, stateless pod replicas**. You tell it which container image to run, how many copies, what environment variables to inject, and what health checks to run. Kubernetes ensures that the requested number of replicas is always running. If a pod crashes, Kubernetes replaces it automatically.

Key spec sections:

```yaml
spec:
  replicas: 2                    # how many pod copies to maintain
  selector: ...                  # which pods belong to this deployment
  template:                      # the pod template
    spec:
      containers:
        - name: backend
          image: myacr.azurecr.io/backend:abc123
          ports:
            - containerPort: 8000
          envFrom:               # inject all keys from a ConfigMap or Secret
            - configMapRef:
                name: backend-config
            - secretRef:
                name: backend-secret
          livenessProbe: ...     # when to restart the container
          readinessProbe: ...    # when to start sending traffic to it
      initContainers:            # run once before main containers start
        - name: migrate
          command: ["alembic", "upgrade", "head"]
```

### `Service`

**Files:** `backend-service.yaml`, `frontend-service.yaml`, `postgres-service.yaml`, `elasticsearch-service.yaml`, `kibana-service.yaml`

A Service gives a **stable DNS name and IP address** to a set of pods. Pods are ephemeral — they come and go, and their IP addresses change. A Service is permanent. Other components always talk to the Service, never to pod IPs directly.

```yaml
spec:
  selector:
    app: backend            # routes traffic to pods with this label
  ports:
    - port: 8000            # the port the Service listens on
      targetPort: 8000      # the port on the pod to forward to
```

### `ConfigMap`

**File:** `backend-configmap.yaml`

A ConfigMap stores **non-sensitive configuration** as key-value pairs. The backend reads `APP_MODE`, `CORS_ORIGINS`, `DEFAULT_KEYWORDS`, and `ELASTICSEARCH_URL` from environment variables — these are injected from the ConfigMap at pod startup.

### `Secret`

**Files:** `backend-secret.yaml`, `postgres-secret.yaml`

A Secret is like a ConfigMap but for **sensitive data**. Kubernetes stores Secret values base64-encoded (not encrypted by default, but they are kept separate from ConfigMaps and can be encrypted at rest via Azure Key Vault integration). The database URL and Postgres credentials live here.

### `PersistentVolumeClaim` (PVC)

**Files:** `postgres-pvc.yaml`, `elasticsearch-pvc.yaml`

A PVC is a **request for persistent storage**. Containers are ephemeral — anything written to their filesystem is lost when the pod restarts. A PVC asks the cluster for a volume of a given size that survives pod restarts. In AKS, Azure Disk or Azure Files is provisioned automatically when a PVC is created.

```yaml
spec:
  accessModes:
    - ReadWriteOnce    # one pod at a time can mount this volume
  resources:
    requests:
      storage: 20Gi
```

### `Ingress`

**File:** `ingress.yaml`

An Ingress is a **cluster-level HTTP router**. It receives traffic from outside the cluster and routes it to the right internal Service based on the URL path:

- `/api/*` → backend Service (port 8000)
- `/*` → frontend Service (port 80)

An Ingress requires an **Ingress Controller** to be installed in the cluster (this chart uses NGINX). The Ingress just defines the routing rules; the controller is the actual load balancer that enforces them.

The ingress in this chart also configures:
- TLS termination (per environment, when `frontend.ingress.tls.enabled: true`)
- Extended proxy timeouts to support WebSocket long-polling on `/api/ws/alerts`

---

## 5. The `type` field — subtypes on specific resources

Two resource types have a `type` sub-field that changes their behaviour.

### Service `type`

```yaml
kind: Service
spec:
  type: ClusterIP   # or NodePort, LoadBalancer
```

| Value | Meaning |
|-------|---------|
| `ClusterIP` | The Service is accessible **only inside the cluster** via its DNS name. This is what all services in this chart use — they are all internal. External traffic enters only through the Ingress |
| `NodePort` | Also exposes a port on every cluster node. Useful for testing without an Ingress controller |
| `LoadBalancer` | Provisions a cloud load balancer with a public IP. Not used here because the Ingress controller already handles external traffic |

### Secret `type`

```yaml
kind: Secret
type: Opaque
```

| Value | Meaning |
|-------|---------|
| `Opaque` | Generic unstructured secret. Use this for application secrets like database URLs and passwords — anything that doesn't fit a built-in type |
| `kubernetes.io/tls` | Stores a TLS certificate and private key. Used by the Ingress for HTTPS termination. Created separately (by cert-manager or manually) |
| `kubernetes.io/dockerconfigjson` | Stores Docker registry credentials. Used by pods to pull private images |

---

## 6. Template files — one by one

### `_helpers.tpl`

A special Helm file. It is **never rendered into a Kubernetes manifest**. Instead, it defines reusable named templates (Helm macros) that other template files can call with `{{ include }}`.

Named templates defined here:

| Template name | What it returns |
|---------------|-----------------|
| `news-crawler.name` | The chart name, truncated to 63 characters (Kubernetes label limit) |
| `news-crawler.fullname` | `<release-name>-<chart-name>`, also truncated |
| `news-crawler.labels` | Standard labels applied to every resource: `app.kubernetes.io/name`, `app.kubernetes.io/instance`, `helm.sh/chart`, `app.kubernetes.io/managed-by` |
| `news-crawler.selectorLabels` | Subset of labels used in `selector` and pod `template.metadata.labels` to match pods to Services and Deployments |
| `news-crawler.elasticsearch.url` | Auto-constructs `http://<release>-elasticsearch:9200` when Elasticsearch is enabled internally |
| `news-crawler.database.url` | Auto-constructs the full `postgresql+asyncpg://...` connection URL from Postgres values when not overridden |

Using shared helpers keeps all resource names consistent and eliminates copy-paste errors across 17 template files.

---

### ConfigMap

**File:** `backend-configmap.yaml`

Injects non-sensitive environment variables into the backend container:

| Key | Value source | Purpose |
|-----|-------------|---------|
| `APP_MODE` | `backend.config.appMode` | `prod` disables `/docs` and `/openapi.json`; `dev` enables them |
| `CORS_ORIGINS` | `backend.config.corsOrigins` | Comma-separated list of allowed browser origins |
| `DEFAULT_KEYWORDS` | `backend.config.defaultKeywords` | Seed keywords loaded at startup |
| `ELASTICSEARCH_URL` | `news-crawler.elasticsearch.url` helper | Auto-resolved to the internal ES service URL |

---

### Secret

**File:** `backend-secret.yaml`  
**File:** `postgres-secret.yaml`

`backend-secret.yaml` stores the `DATABASE_URL` (a full `postgresql+asyncpg://` connection string). It is of type `Opaque` and uses `stringData` so you can write plain strings without manually base64-encoding them — Helm/Kubernetes handles the encoding.

`postgres-secret.yaml` stores `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` for the Postgres container itself.

---

### Deployment

| File | Container | Notable details |
|------|-----------|----------------|
| `backend-deployment.yaml` | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Has an **init container** that runs `alembic upgrade head` before the app starts, ensuring the DB schema is always up to date. `replicaCount` must stay at **1** — the APScheduler runs inside the FastAPI process and would create duplicate jobs if scaled |
| `frontend-deployment.yaml` | nginx serving the built Vue SPA on port 80 | No init container needed; purely static |
| `postgres-deployment.yaml` | `postgres:16-alpine` | `strategy.type: Recreate` — stops the old pod fully before starting the new one, required because a PVC can only be mounted by one pod at a time (`ReadWriteOnce`) |
| `elasticsearch-deployment.yaml` | `elasticsearch:8.15.0` | `discovery.type: single-node`, security disabled for simplicity. `node.store.allow_mmap: false` avoids AKS virtual-memory limits |
| `kibana-deployment.yaml` | `kibana:8.15.0` | Conditional on `kibana.enabled`. Enabled in dev and test, disabled in prod |

---

### Service

All five Services (`backend`, `frontend`, `postgres`, `elasticsearch`, `kibana`) use `type: ClusterIP`. This means they are only reachable inside the cluster. Communication flow:

```
Internet
  │
  ▼
Ingress (NGINX)
  ├── /api/*  ──► backend-service :8000
  └── /*      ──► frontend-service :80

backend-service
  └──► backend pod
         ├── postgres-service :5432
         └── elasticsearch-service :9200
```

---

### PersistentVolumeClaim

| File | Used by | Default size | Notes |
|------|---------|-------------|-------|
| `postgres-pvc.yaml` | postgres Deployment | 5 Gi (dev off, test 4 Gi, prod 20 Gi) | `ReadWriteOnce` — single-pod access |
| `elasticsearch-pvc.yaml` | elasticsearch Deployment | 10 Gi (dev off, test 5 Gi, prod 30 Gi) | `fsGroup: 1000` in pod security context so Elasticsearch can write to the mounted path |

Both PVCs are conditional: `persistence.enabled: false` in dev skips PVC creation and uses an ephemeral `emptyDir` instead, so dev deployments have no persistent state and are easy to reset.

---

### Ingress

**File:** `ingress.yaml`

Uses the NGINX ingress controller (`ingressClassName: nginx`) and defines two path rules:

```
host: news-monitor.example.com
  /api  →  backend-service:8000   (PathType: Prefix)
  /     →  frontend-service:80    (PathType: Prefix)
```

Additional annotations:
- `nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"` — keeps the connection open for 1 hour, required for the WebSocket endpoint at `/api/ws/alerts`
- `nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"` — same, for the send direction

TLS block is conditional (`frontend.ingress.tls.enabled`). When enabled, NGINX terminates HTTPS using the certificate stored in the named Kubernetes TLS Secret. In test and prod this should be provisioned by cert-manager with a Let's Encrypt `ClusterIssuer`.
