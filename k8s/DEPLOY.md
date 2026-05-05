# Deployment Setup Guide

Step-by-step instructions for wiring up the GitHub Actions CI/CD pipeline and deploying the news crawler to Azure Kubernetes Service.

---

## Prerequisites

Before you start, make sure the following Azure resources already exist:

- An Azure subscription
- An Azure Container Registry (ACR) instance
- An Azure Kubernetes Service (AKS) cluster with the NGINX ingress controller installed
- A service principal that has at minimum:
  - `AcrPush` role on the ACR instance
  - `Azure Kubernetes Service Cluster User Role` on the AKS cluster

If any of these are missing, follow the Azure portal or CLI guides to create them first.

---

## Step 1 — Create the Azure service principal

The workflow authenticates to Azure using a JSON credential block stored as a GitHub secret. Generate it once per environment (or share it if all environments live in the same subscription and the principal has access to all clusters).

```bash
az ad sp create-for-rbac \
  --name "news-crawler-github-actions" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP> \
  --sdk-auth
```

Copy the entire JSON output. You will paste it as the `AZURE_CREDENTIALS` secret in the next step.

The output looks like:

```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  ...
}
```

---

## Step 2 — Grant the service principal ACR push access

```bash
az role assignment create \
  --assignee <clientId from above> \
  --role AcrPush \
  --scope $(az acr show --name <ACR_NAME> --query id -o tsv)
```

---

## Step 3 — Create GitHub Environments

The workflow uses GitHub Environments so that secrets and variables are scoped per deployment target.

1. Open your repository on GitHub.
2. Go to **Settings → Environments**.
3. Click **New environment** and create three environments, one at a time:
   - `dev`
   - `test`
   - `prod`

No additional protection rules are required for `dev`. For `test` and `prod`, you may want to add required reviewers under **Deployment protection rules**.

---

## Step 4 — Add secrets to each environment

For each of the three environments (`dev`, `test`, `prod`), go to **Settings → Environments → \<name\> → Add secret** and add the following:

### `AZURE_CREDENTIALS`

| Environment | Value |
|-------------|-------|
| `dev`       | The JSON output from Step 1 for the dev service principal |
| `test`      | The JSON output from Step 1 for the test service principal |
| `prod`      | The JSON output from Step 1 for the prod service principal |

You can use the same service principal for all three if they share a subscription and resource group, as long as it has the required roles on every cluster and registry it needs to reach.

### `POSTGRES_PASSWORD`

| Environment | Recommended value |
|-------------|-------------------|
| `dev`       | Any local password, e.g. `dev-local-pass` |
| `test`      | A strong generated password, e.g. from `openssl rand -base64 24` |
| `prod`      | A strong generated password, stored in a password manager |

Do **not** use the placeholder values from the values files in real deployments.

---

## Step 5 — Add variables to each environment

For each environment, go to **Settings → Environments → \<name\> → Add variable** and add the following four variables.

### `AZURE_RESOURCE_GROUP`

The name of the Azure resource group that contains your AKS cluster.

| Environment | Example value |
|-------------|---------------|
| `dev`       | `rg-news-crawler-dev` |
| `test`      | `rg-news-crawler-test` |
| `prod`      | `rg-news-crawler-prod` |

### `AZURE_AKS_CLUSTER_NAME`

The name of the AKS cluster in that resource group.

| Environment | Example value |
|-------------|---------------|
| `dev`       | `aks-news-dev` |
| `test`      | `aks-news-test` |
| `prod`      | `aks-news-prod` |

### `AZURE_CONTAINER_REGISTRY`

The **short name** of the ACR instance (not the login server URL — without `.azurecr.io`).

| Environment | Example value |
|-------------|---------------|
| `dev`       | `newscrawleracr` |
| `test`      | `newscrawleracr` |
| `prod`      | `newscrawleracr` |

All environments can share one registry. Each image push is tagged with the Git SHA so there are no collisions.

### `AKS_INGRESS_HOST`

The public hostname that will be used for the ingress rule (no scheme prefix, no trailing slash).

| Environment | Example value |
|-------------|---------------|
| `dev`       | `news-monitor.dev` or the IP of the ingress controller |
| `test`      | `news-monitor.test.example.com` |
| `prod`      | `news-monitor.example.com` |

The workflow builds the CORS origin automatically by prepending `http://` for dev and `https://` for test and prod.

---

## Step 6 — Configure branch protection (optional but recommended)

The workflow fires on three branches:

| Branch    | Deploys to |
|-----------|------------|
| `develop` | `dev` environment |
| `staging` | `test` environment |
| `main`    | `prod` environment |

Go to **Settings → Branches → Add branch protection rule** for `main` and `staging` to require pull-request reviews before merging, which prevents accidental direct pushes to test and production.

---

## Step 7 — Verify the workflow file is in the repository

The workflow file must exist at exactly this path:

```
.github/workflows/deploy-aks.yml
```

It is already committed as part of this repository. No further action is needed unless you rename or move it.

---

## Step 8 — Review the values files before the first deployment

Before merging to any branch, open the environment values file for that environment and verify the placeholder values are appropriate.

### `k8s/news-crawler/values.dev.yaml`

| Key | Current placeholder | What to set |
|-----|--------------------|----|
| `frontend.ingress.host` | `news-monitor.dev` | IP or DNS of your local ingress |
| `backend.config.corsOrigins` | `http://localhost:3000,...` | Adjust if your dev ingress host differs |
| `postgres.password` | `dev-password` | Overridden by `POSTGRES_PASSWORD` secret in CI; only used for local manual deploys |

### `k8s/news-crawler/values.test.yaml`

| Key | Current placeholder | What to set |
|-----|--------------------|----|
| `frontend.ingress.host` | `news-monitor.test.example.com` | Your actual test hostname |
| `backend.config.corsOrigins` | `https://news-monitor.test.example.com` | Must match the ingress host |
| `frontend.ingress.tls.secretName` | `news-monitor-test-tls` | Name of the TLS secret in the cluster; provision with cert-manager or manually |
| `postgres.password` | `change-me-test` | Overridden by `POSTGRES_PASSWORD` secret in CI |

### `k8s/news-crawler/values.prod.yaml`

| Key | Current placeholder | What to set |
|-----|--------------------|----|
| `frontend.ingress.host` | `news-monitor.example.com` | Your actual production hostname |
| `backend.config.corsOrigins` | `https://news-monitor.example.com` | Must match the ingress host |
| `frontend.ingress.tls.secretName` | `news-monitor-prod-tls` | Name of the TLS secret in the cluster |
| `postgres.password` | `change-me` | Overridden by `POSTGRES_PASSWORD` secret in CI |
| `postgres.persistence.size` | `20Gi` | Adjust to expected data volume |
| `elasticsearch.persistence.size` | `30Gi` | Adjust to expected index size |

---

## Step 9 — First deployment

Push a commit to the target branch. GitHub Actions will:

1. Resolve the environment parameters from the branch name.
2. Log into Azure using `AZURE_CREDENTIALS`.
3. Connect to the AKS cluster.
4. Build the backend and frontend Docker images.
5. Push both images to ACR tagged with the first 12 characters of the Git SHA.
6. Run `helm upgrade --install` layering `values.yaml` then the environment values file, then injecting secrets via `--set-string`.

You can also trigger a deployment manually at any time from **Actions → Deploy To AKS → Run workflow** and pick the target environment from the dropdown.

---

## Step 10 — TLS certificates (test and prod)

The test and prod values files have `frontend.ingress.tls.enabled: true`. The ingress expects a Kubernetes Secret of type `kubernetes.io/tls` with the name configured in `frontend.ingress.tls.secretName`.

### Option A — cert-manager (recommended)

Install cert-manager in the cluster and create a `ClusterIssuer`. Then uncomment the cert-manager annotation in the production values file:

```yaml
frontend:
  ingress:
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
```

cert-manager will automatically provision and renew the certificate.

### Option B — Manual secret

```bash
kubectl create secret tls news-monitor-prod-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  --namespace news-crawler
```

---

## Reference: complete variable and secret checklist

Use this table as a final verification checklist before running the pipeline for the first time.

### Secrets (Settings → Environments → \<env\> → Secrets)

| Secret name | Required in | Description |
|-------------|-------------|-------------|
| `AZURE_CREDENTIALS` | `dev`, `test`, `prod` | Service principal JSON from Step 1 |
| `POSTGRES_PASSWORD` | `dev`, `test`, `prod` | Database password for that environment |

### Variables (Settings → Environments → \<env\> → Variables)

| Variable name | Required in | Description |
|---------------|-------------|-------------|
| `AZURE_RESOURCE_GROUP` | `dev`, `test`, `prod` | Azure resource group name |
| `AZURE_AKS_CLUSTER_NAME` | `dev`, `test`, `prod` | AKS cluster name |
| `AZURE_CONTAINER_REGISTRY` | `dev`, `test`, `prod` | ACR short name (no `.azurecr.io`) |
| `AKS_INGRESS_HOST` | `dev`, `test`, `prod` | Public hostname without scheme |

### Values file placeholders still requiring your attention

| File | Key | Must be updated |
|------|-----|-----------------|
| `values.dev.yaml` | `frontend.ingress.host` | Yes, if the dev cluster has a real hostname |
| `values.test.yaml` | `frontend.ingress.host` | Yes |
| `values.test.yaml` | `frontend.ingress.tls.secretName` | Yes, create the TLS secret first |
| `values.prod.yaml` | `frontend.ingress.host` | Yes |
| `values.prod.yaml` | `frontend.ingress.tls.secretName` | Yes, create the TLS secret first |
| `values.prod.yaml` | `postgres.persistence.size` | Review before first deploy |
| `values.prod.yaml` | `elasticsearch.persistence.size` | Review before first deploy |
