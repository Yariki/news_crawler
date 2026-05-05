# Kubernetes Deployment Guide

This folder contains the Helm-based Kubernetes deployment for the news crawler application.

## Structure

### Root

- `news-crawler/` - Helm chart for deploying the application stack.

### Chart files

- `news-crawler/Chart.yaml` - Helm chart metadata: chart name, type, version, and app version.
- `news-crawler/values.yaml` - Default configuration values used by all templates.
- `news-crawler/values.dev.yaml` - Development overrides: persistence off, minimal resources, Kibana enabled, docs endpoints on.
- `news-crawler/values.test.yaml` - Test / staging overrides: persistence on, reduced size, Kibana enabled, docs endpoints on.
- `news-crawler/values.prod.yaml` - Production overrides: TLS enabled, full resource limits, Kibana off, docs endpoints off.

### Template files

- `news-crawler/templates/_helpers.tpl` - Shared Helm helper functions for names, labels, service names, and derived URLs.
- `news-crawler/templates/backend-configmap.yaml` - Non-sensitive backend runtime settings such as `APP_MODE`, `CORS_ORIGINS`, `DEFAULT_KEYWORDS`, and `ELASTICSEARCH_URL`.
- `news-crawler/templates/backend-secret.yaml` - Sensitive backend runtime settings, currently the database connection string.
- `news-crawler/templates/backend-deployment.yaml` - Backend deployment with one init container for Alembic migrations and one FastAPI container.
- `news-crawler/templates/backend-service.yaml` - Internal ClusterIP service for the backend API.
- `news-crawler/templates/frontend-deployment.yaml` - Frontend deployment serving the built Vue app from NGINX.
- `news-crawler/templates/frontend-service.yaml` - Internal ClusterIP service for the frontend.
- `news-crawler/templates/ingress.yaml` - External ingress that routes `/` to frontend and `/api` to backend.
- `news-crawler/templates/postgres-secret.yaml` - PostgreSQL credentials and database name.
- `news-crawler/templates/postgres-pvc.yaml` - PersistentVolumeClaim for PostgreSQL data.
- `news-crawler/templates/postgres-deployment.yaml` - Single-replica PostgreSQL deployment.
- `news-crawler/templates/postgres-service.yaml` - Internal ClusterIP service for PostgreSQL.
- `news-crawler/templates/elasticsearch-pvc.yaml` - PersistentVolumeClaim for Elasticsearch data.
- `news-crawler/templates/elasticsearch-deployment.yaml` - Single-node Elasticsearch deployment with persistence.
- `news-crawler/templates/elasticsearch-service.yaml` - Internal ClusterIP service for Elasticsearch.
- `news-crawler/templates/kibana-deployment.yaml` - Optional Kibana deployment, disabled by default.
- `news-crawler/templates/kibana-service.yaml` - Internal ClusterIP service for Kibana.

## What This Chart Deploys

By default, the chart deploys:

- frontend
- backend
- PostgreSQL
- Elasticsearch

Optional component:

- Kibana, if `kibana.enabled=true`

## Basic Helm Concepts Used Here

This chart uses a small set of standard Helm mechanisms:

- `values.yaml` stores default configuration.
- templates in `templates/` render Kubernetes manifests from those values.
- helper templates in `_helpers.tpl` avoid repeating names and labels.
- `helm upgrade --install` is used for both first deployment and updates.
- `--set` or `--set-string` can override individual values during deploy time.

The chart is intentionally simple and close to the current Docker Compose architecture.

## Configuration Model Used Here

### 1. Application images

Both frontend and backend images are configurable through:

- `backend.image.repository`
- `backend.image.tag`
- `frontend.image.repository`
- `frontend.image.tag`

This is what the GitHub Actions workflow updates on each deployment.

### 2. Ingress-based routing

The frontend and backend are exposed behind a single host:

- `/` goes to frontend
- `/api` goes to backend

That is why the frontend was changed to use same-host API and WebSocket routing by default.

Relevant values:

- `frontend.ingress.enabled`
- `frontend.ingress.className`
- `frontend.ingress.host`
- `frontend.ingress.annotations`
- `frontend.ingress.tls.*`

### 3. Backend runtime settings

The backend reads environment variables. This chart splits them by sensitivity:

- non-sensitive values go to `backend-configmap.yaml`
- sensitive values go to `backend-secret.yaml`

Relevant values:

- `backend.config.appMode`
- `backend.config.corsOrigins`
- `backend.config.defaultKeywords`
- `backend.config.elasticsearchUrl`
- `backend.secret.databaseUrl`

If `backend.secret.databaseUrl` is empty and `postgres.enabled=true`, the chart builds the database URL automatically.

If `backend.config.elasticsearchUrl` is empty and `elasticsearch.enabled=true`, the chart builds the Elasticsearch URL automatically.

### 4. Embedded data services

This chart currently deploys PostgreSQL and Elasticsearch inside the same release.

Relevant values:

- `postgres.enabled`
- `postgres.database`
- `postgres.username`
- `postgres.password`
- `postgres.persistence.*`
- `elasticsearch.enabled`
- `elasticsearch.javaOpts`
- `elasticsearch.persistence.*`

If you already have managed PostgreSQL or Elasticsearch outside the cluster, disable the embedded service and provide the external connection values instead.

### 5. Persistence

Persistent storage is enabled for PostgreSQL and Elasticsearch by default.

Relevant values:

- `global.storageClass`
- `postgres.persistence.enabled`
- `postgres.persistence.size`
- `elasticsearch.persistence.enabled`
- `elasticsearch.persistence.size`

If `global.storageClass` is empty, Kubernetes uses the cluster default storage class.

### 6. Resources

Each main component has a `resources` block, currently empty by default:

- `backend.resources`
- `frontend.resources`
- `postgres.resources`
- `elasticsearch.resources`
- `kibana.resources`

You can define CPU and memory requests and limits there.

## Important Behavioral Note

The backend application starts APScheduler inside the FastAPI application lifecycle. Because of that, `backend.replicaCount` should stay `1` unless scheduling is moved into a dedicated worker or separate service.

If you scale the backend deployment without changing that architecture, scheduled jobs can run multiple times.

## How To Use This Helm Chart

### Render manifests locally

From repository root:

```bash
helm template news-crawler ./k8s/news-crawler
```

This renders Kubernetes manifests without applying anything to the cluster.

### Install or upgrade manually

```bash
helm upgrade --install news-crawler ./k8s/news-crawler \
  --namespace news-crawler \
  --create-namespace
```

### Override values from command line

Example:

```bash
helm upgrade --install news-crawler ./k8s/news-crawler \
  --namespace news-crawler \
  --create-namespace \
  --set-string frontend.ingress.host=news.example.com \
  --set-string backend.config.corsOrigins=https://news.example.com \
  --set-string backend.image.repository=myregistry.azurecr.io/news-crawler-backend \
  --set-string backend.image.tag=20260505 \
  --set-string frontend.image.repository=myregistry.azurecr.io/news-crawler-frontend \
  --set-string frontend.image.tag=20260505 \
  --set-string postgres.password=replace-me
```

### Deploy to development (local cluster)

```bash
helm upgrade --install news-crawler ./k8s/news-crawler \
  --namespace news-crawler-dev \
  --create-namespace \
  -f ./k8s/news-crawler/values.yaml \
  -f ./k8s/news-crawler/values.dev.yaml \
  --set-string backend.image.repository=myregistry.azurecr.io/news-crawler-backend \
  --set-string backend.image.tag=local \
  --set-string frontend.image.repository=myregistry.azurecr.io/news-crawler-frontend \
  --set-string frontend.image.tag=local
```

What dev values do:

- persistence disabled (data is lost on pod restart, keeps the cluster clean)
- `appMode: dev` turns on `/docs`, `/redoc`, `/openapi.json`
- Kibana is enabled
- resource requests and limits are minimal

### Deploy to test / staging

```bash
helm upgrade --install news-crawler ./k8s/news-crawler \
  --namespace news-crawler-test \
  --create-namespace \
  -f ./k8s/news-crawler/values.yaml \
  -f ./k8s/news-crawler/values.test.yaml \
  --set-string backend.image.repository=myregistry.azurecr.io/news-crawler-backend \
  --set-string backend.image.tag=20260505-abc123 \
  --set-string frontend.image.repository=myregistry.azurecr.io/news-crawler-frontend \
  --set-string frontend.image.tag=20260505-abc123 \
  --set-string postgres.password=my-test-password
```

What test values do:

- persistence enabled with smaller volumes (4 Gi / 5 Gi)
- `appMode: dev` keeps docs endpoints available for QA
- Kibana enabled
- separate database name and user from production

### Deploy to production

```bash
helm upgrade --install news-crawler ./k8s/news-crawler \
  --namespace news-crawler \
  --create-namespace \
  -f ./k8s/news-crawler/values.yaml \
  -f ./k8s/news-crawler/values.prod.yaml \
  --set-string backend.image.repository=myregistry.azurecr.io/news-crawler-backend \
  --set-string backend.image.tag=20260505-abc123 \
  --set-string frontend.image.repository=myregistry.azurecr.io/news-crawler-frontend \
  --set-string frontend.image.tag=20260505-abc123 \
  --set-string frontend.ingress.host=news.example.com \
  --set-string backend.config.corsOrigins=https://news.example.com \
  --set-string postgres.password=strong-prod-secret
```

What prod values do:

- `appMode: prod` disables all API docs endpoints
- TLS enabled on ingress
- frontend runs 2 replicas
- Kibana disabled
- larger persistent volumes (20 Gi / 30 Gi)
- Elasticsearch JVM heap increased to 1 Gi
- full CPU and memory resource limits for all components

### How multiple values files are merged

Helm merges values files left to right: each `-f` file overrides the same key from the previous one, and `--set-string` flags override everything.

```
values.yaml  ←  values.<env>.yaml  ←  --set-string ...
```

This means `values.yaml` keeps the base defaults, and each environment file only overrides the keys that differ from the base.

## Recommended First Production Overrides

At minimum, review and override these values before a real deployment:

- `frontend.ingress.host`
- `backend.config.corsOrigins`
- `postgres.password`
- `backend.image.repository`
- `backend.image.tag`
- `frontend.image.repository`
- `frontend.image.tag`
- `global.storageClass`, if AKS default storage class is not what you want
- `backend.resources`
- `frontend.resources`
- `postgres.resources`
- `elasticsearch.resources`

## GitHub Actions Integration

The GitHub Actions workflow at `.github/workflows/deploy-aks.yml` has two jobs:

- `resolve-env` — determines the target environment and its parameters from the branch name or manual input, emitting them as job outputs.
- `deploy` — logs into Azure, builds and pushes both images to ACR, then runs `helm upgrade --install` using the base `values.yaml` layered with the environment-specific values file.

### Branch to environment mapping

| Branch    | Environment | Namespace            | Values file               |
|-----------|-------------|----------------------|---------------------------|
| `develop` | `dev`       | `news-crawler-dev`   | `values.dev.yaml`         |
| `staging` | `test`      | `news-crawler-test`  | `values.test.yaml`        |
| `main`    | `prod`      | `news-crawler`       | `values.prod.yaml`        |

A manual run (`workflow_dispatch`) lets you pick any environment via the input dropdown.

### GitHub Environments

The `deploy` job sets `environment: <name>` which tells GitHub Actions to use secrets and variables scoped to that GitHub Environment. Create three GitHub Environments in **Settings → Environments**: `dev`, `test`, `prod`.

Each environment must define the following:

**Secrets:**

| Name                  | Description                                              |
|-----------------------|----------------------------------------------------------|
| `AZURE_CREDENTIALS`   | Service principal JSON with AKS and ACR permissions      |
| `POSTGRES_PASSWORD`   | Database password for this environment                   |

**Variables:**

| Name                        | Description                                          |
|-----------------------------|------------------------------------------------------|
| `AZURE_RESOURCE_GROUP`      | Resource group containing the AKS cluster            |
| `AZURE_AKS_CLUSTER_NAME`    | AKS cluster name                                     |
| `AZURE_CONTAINER_REGISTRY`  | ACR name (short name, not the login server URL)      |
| `AKS_INGRESS_HOST`          | Public hostname for the ingress (without scheme)     |

Because each environment can point to a different AKS cluster and ACR, you can isolate dev, test, and production entirely.

## Notes About Scope

This chart matches the current application shape and is suitable for a first AKS deployment. It is not yet a high-availability production architecture.

Main limitations of the current chart:

- backend scheduling is not isolated from the API process
- PostgreSQL is deployed as a single pod inside the cluster
- Elasticsearch is deployed as a single node

If needed, the next iteration should usually be:

1. move scheduler into a separate worker deployment or CronJob
2. replace in-cluster PostgreSQL with Azure Database for PostgreSQL
3. replace in-cluster Elasticsearch with a managed search/logging service or a dedicated multi-node setup