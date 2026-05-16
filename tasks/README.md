# Auth, RBAC & Admin Panel — GitHub Issue Generator

This bundle creates **20 GitHub issues**, **7 milestones** (one per phase), a **label set**, and a **GitHub Project (v2) board** with all issues added — for implementing authentication, role-based authorization, and an admin panel in a **FastAPI + Vue.js** app.

## Contents

```
.
├── create_github_tasks.sh       # main script
├── issues/                      # 20 issue body files (Markdown)
│   ├── 01_auth_schema.md
│   ├── 02_owner_id.md
│   ├── ... (18 more)
│   └── 20_documentation.md
└── README.md                    # this file
```

## Prerequisites

1. **Install `gh` CLI**: https://cli.github.com/
2. **Authenticate** with the right scopes:
   ```bash
   gh auth login
   # If you already logged in but lack the project scope:
   gh auth refresh -s project,read:project
   ```
3. **Install `jq`** (used to parse JSON from `gh` output) — most systems have it; if not: `apt install jq` / `brew install jq`.

## Usage

```bash
chmod +x create_github_tasks.sh
./create_github_tasks.sh <owner/repo> ["Project Title"]
```

### Example

```bash
./create_github_tasks.sh myuser/myapp "Auth & RBAC"
```

That will:
1. Create labels (phase, area, type)
2. Create 7 milestones (one per phase)
3. Create 20 issues, each assigned to its phase milestone with appropriate labels
4. Create a Project (v2) board titled `Auth & RBAC` (defaults to "Auth, RBAC & Admin Panel" if no title given)
5. Add every created issue to the project

## Phases overview

| Phase | Focus |
|------:|-------|
| 1 | Foundation & Database (schema, `owner_id` rollout) |
| 2 | Backend Authentication (passwords, JWT, dependencies) |
| 3 | Backend Authorization (RBAC dependencies, ownership) |
| 4 | Admin API (user & role management endpoints) |
| 5 | Frontend Authentication (Pinia, login views, interceptors, router guards) |
| 6 | Admin Panel UI (layout, users UI, roles UI) |
| 7 | Quality & Security (tests, hardening, docs) |

## Customizing

- **Edit issue content**: open any `issues/NN_*.md` and edit the body. The first line (`# Title`) becomes the issue title.
- **Add/remove labels**: edit the `LABELS` map and `ISSUE_LABELS` mapping in `create_github_tasks.sh`.
- **Skip the project**: comment out the "Create Project (v2)" block in the script.
- **Re-run safely**: labels and milestones are idempotent. Issues are **not** — re-running will create duplicates. If you need to re-run, close/delete the previous issues first.

## Notes

- The script tries to create the project under the same `owner` as the repo. Projects v2 can be owned by users or orgs — `gh` handles both, but the URL format differs (the script prints both possibilities at the end).
- If you don't want a Project board at all, skip the `project` scope and the script will continue with just issues + milestones.
- If your `gh` token is missing the `project` scope, the script will print a hint and continue without creating the project.
