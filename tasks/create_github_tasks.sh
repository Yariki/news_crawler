#!/usr/bin/env bash
# create_github_tasks.sh
#
# Creates labels, milestones (one per phase), issues, and a GitHub Project (v2)
# board for an Auth + RBAC + Admin Panel feature in a FastAPI + Vue.js project.
#
# REQUIREMENTS:
#   - gh CLI installed and authenticated: https://cli.github.com/
#   - gh auth login (with `repo` and `project` scopes)
#     If you already logged in without `project`, run:
#       gh auth refresh -s project,read:project
#
# USAGE:
#   chmod +x create_github_tasks.sh
#   ./create_github_tasks.sh <owner/repo> [project_title]
#
# EXAMPLE:
#   ./create_github_tasks.sh myuser/myrepo "Auth & RBAC"

set -euo pipefail

# ---------- Args ----------
REPO="${1:-}"
PROJECT_TITLE="${2:-Auth, RBAC & Admin Panel}"

if [[ -z "$REPO" ]]; then
  echo "Usage: $0 <owner/repo> [project_title]"
  echo "Example: $0 myuser/myrepo \"Auth & RBAC\""
  exit 1
fi

OWNER="${REPO%%/*}"
REPO_NAME="${REPO##*/}"

ISSUES_DIR="$(cd "$(dirname "$0")" && pwd)/issues"
if [[ ! -d "$ISSUES_DIR" ]]; then
  echo "ERROR: issues directory not found at $ISSUES_DIR"
  exit 1
fi

echo "==> Repo:    $REPO"
echo "==> Project: $PROJECT_TITLE"
echo "==> Issues:  $ISSUES_DIR"
echo ""

# ---------- Detect if owner is an org or user ----------
# Project v2 is owned by a user OR an org. Try org first, then user.
PROJECT_OWNER_FLAG="--owner $OWNER"

# ---------- 1. Create labels ----------
echo "==> Creating labels..."
declare -A LABELS=(
  ["phase:1-foundation"]="0E8A16"
  ["phase:2-auth-backend"]="1D76DB"
  ["phase:3-authz-backend"]="5319E7"
  ["phase:4-admin-api"]="B60205"
  ["phase:5-auth-frontend"]="FBCA04"
  ["phase:6-admin-ui"]="D93F0B"
  ["phase:7-quality"]="0052CC"
  ["area:backend"]="C5DEF5"
  ["area:frontend"]="BFD4F2"
  ["area:database"]="C2E0C6"
  ["area:security"]="E99695"
  ["area:devops"]="D4C5F9"
  ["type:feature"]="A2EEEF"
  ["type:chore"]="CCCCCC"
  ["type:docs"]="0075CA"
  ["type:test"]="FEF2C0"
)

for label in "${!LABELS[@]}"; do
  color="${LABELS[$label]}"
  # --force overwrites color/description if label exists
  gh label create "$label" \
    --repo "$REPO" \
    --color "$color" \
    --force >/dev/null 2>&1 \
    && echo "    ✓ $label" \
    || echo "    ! $label (skipped — may already exist with different settings)"
done
echo ""

# ---------- 2. Create milestones (one per phase) ----------
echo "==> Creating milestones..."
declare -a MILESTONES=(
  "Phase 1: Foundation & Database"
  "Phase 2: Backend Authentication"
  "Phase 3: Backend Authorization"
  "Phase 4: Admin API"
  "Phase 5: Frontend Authentication"
  "Phase 6: Admin Panel UI"
  "Phase 7: Quality & Security"
)

declare -A MILESTONE_NUMBERS=()

for title in "${MILESTONES[@]}"; do
  # Try to get existing milestone number
  existing=$(gh api "repos/$REPO/milestones?state=all" --jq ".[] | select(.title==\"$title\") | .number" 2>/dev/null || echo "")
  if [[ -n "$existing" ]]; then
    MILESTONE_NUMBERS["$title"]="$existing"
    echo "    = $title (already exists, #$existing)"
  else
    number=$(gh api "repos/$REPO/milestones" \
      --method POST \
      -f title="$title" \
      --jq '.number')
    MILESTONE_NUMBERS["$title"]="$number"
    echo "    ✓ $title (#$number)"
  fi
done
echo ""

# ---------- 3. Create Project (v2) ----------
echo "==> Creating GitHub Project (v2)..."

# Try as org first, fall back to user
PROJECT_NUMBER=""
if gh project create --owner "$OWNER" --title "$PROJECT_TITLE" --format json >/tmp/proj_create.json 2>/dev/null; then
  PROJECT_NUMBER=$(jq -r '.number' /tmp/proj_create.json)
  echo "    ✓ Project created: #$PROJECT_NUMBER ($PROJECT_TITLE)"
else
  # Maybe project already exists
  existing_num=$(gh project list --owner "$OWNER" --format json --limit 100 \
    | jq -r ".projects[] | select(.title==\"$PROJECT_TITLE\") | .number" 2>/dev/null || echo "")
  if [[ -n "$existing_num" ]]; then
    PROJECT_NUMBER="$existing_num"
    echo "    = Project already exists: #$PROJECT_NUMBER"
  else
    echo "    ! Could not create project. Check that your gh token has 'project' scope."
    echo "      Run: gh auth refresh -s project,read:project"
    echo "      Continuing with issues only..."
  fi
fi
echo ""

# ---------- 4. Create issues from files ----------
echo "==> Creating issues..."

# Mapping from issue file prefix -> phase milestone + phase label + areas + types
# Order matters: files are sorted, so 01_, 02_, ... process in order.

declare -A ISSUE_MILESTONE=(
  ["01"]="Phase 1: Foundation & Database"
  ["02"]="Phase 1: Foundation & Database"
  ["03"]="Phase 2: Backend Authentication"
  ["04"]="Phase 2: Backend Authentication"
  ["05"]="Phase 2: Backend Authentication"
  ["06"]="Phase 3: Backend Authorization"
  ["07"]="Phase 3: Backend Authorization"
  ["08"]="Phase 3: Backend Authorization"
  ["09"]="Phase 4: Admin API"
  ["10"]="Phase 4: Admin API"
  ["11"]="Phase 5: Frontend Authentication"
  ["12"]="Phase 5: Frontend Authentication"
  ["13"]="Phase 5: Frontend Authentication"
  ["14"]="Phase 5: Frontend Authentication"
  ["15"]="Phase 6: Admin Panel UI"
  ["16"]="Phase 6: Admin Panel UI"
  ["17"]="Phase 6: Admin Panel UI"
  ["18"]="Phase 7: Quality & Security"
  ["19"]="Phase 7: Quality & Security"
  ["20"]="Phase 7: Quality & Security"
)

declare -A ISSUE_LABELS=(
  ["01"]="phase:1-foundation,area:database,area:backend,type:feature"
  ["02"]="phase:1-foundation,area:database,area:backend,type:chore"
  ["03"]="phase:2-auth-backend,area:backend,type:feature"
  ["04"]="phase:2-auth-backend,area:backend,area:security,type:feature"
  ["05"]="phase:2-auth-backend,area:backend,type:feature"
  ["06"]="phase:3-authz-backend,area:backend,area:security,type:feature"
  ["07"]="phase:3-authz-backend,area:backend,area:security,type:feature"
  ["08"]="phase:3-authz-backend,area:backend,type:chore"
  ["09"]="phase:4-admin-api,area:backend,type:feature"
  ["10"]="phase:4-admin-api,area:backend,type:feature"
  ["11"]="phase:5-auth-frontend,area:frontend,type:feature"
  ["12"]="phase:5-auth-frontend,area:frontend,type:feature"
  ["13"]="phase:5-auth-frontend,area:frontend,type:feature"
  ["14"]="phase:5-auth-frontend,area:frontend,type:feature"
  ["15"]="phase:6-admin-ui,area:frontend,type:feature"
  ["16"]="phase:6-admin-ui,area:frontend,type:feature"
  ["17"]="phase:6-admin-ui,area:frontend,type:feature"
  ["18"]="phase:7-quality,area:backend,area:frontend,type:test"
  ["19"]="phase:7-quality,area:security,area:backend,type:feature"
  ["20"]="phase:7-quality,type:docs"
)

CREATED_ISSUE_URLS=()

for file in $(ls "$ISSUES_DIR"/*.md | sort); do
  filename=$(basename "$file")
  prefix="${filename%%_*}"

  # Title = first line of file (strip leading '# ')
  title=$(head -n 1 "$file" | sed 's/^# *//')
  # Body = everything after the title line
  body=$(tail -n +2 "$file")

  milestone_title="${ISSUE_MILESTONE[$prefix]:-}"
  labels="${ISSUE_LABELS[$prefix]:-}"

  milestone_arg=()
  if [[ -n "$milestone_title" ]]; then
    milestone_arg=(--milestone "$milestone_title")
  fi

  label_arg=()
  if [[ -n "$labels" ]]; then
    label_arg=(--label "$labels")
  fi

  url=$(gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --body "$body" \
    "${milestone_arg[@]}" \
    "${label_arg[@]}")

  echo "    ✓ #$prefix $title"
  echo "        $url"
  CREATED_ISSUE_URLS+=("$url")
done
echo ""

# ---------- 5. Add issues to project ----------
if [[ -n "$PROJECT_NUMBER" ]]; then
  echo "==> Adding issues to project #$PROJECT_NUMBER..."
  for url in "${CREATED_ISSUE_URLS[@]}"; do
    gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" --url "$url" >/dev/null \
      && echo "    ✓ $url" \
      || echo "    ! Failed to add: $url"
  done
  echo ""
  echo "==> Project URL:"
  echo "    https://github.com/users/$OWNER/projects/$PROJECT_NUMBER"
  echo "    (or https://github.com/orgs/$OWNER/projects/$PROJECT_NUMBER if it's an org)"
fi

echo ""
echo "==> Done! Created ${#CREATED_ISSUE_URLS[@]} issues."
