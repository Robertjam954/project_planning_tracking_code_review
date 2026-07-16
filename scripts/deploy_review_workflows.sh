#!/usr/bin/env bash
# Deploy the central Claude code-review workflow into every project repo.
#
# For each repo listed in projects.json (that has one), this:
#   1. clones/pulls a shallow copy into a temp dir
#   2. drops templates/claude-review.yml into .github/workflows/
#   3. sets the ANTHROPIC_API_KEY secret (if ANTHROPIC_API_KEY is in your env)
#   4. commits + pushes on the repo's default branch
#
# Usage:
#   ANTHROPIC_API_KEY=sk-ant-...  ./scripts/deploy_review_workflows.sh
#   ./scripts/deploy_review_workflows.sh --no-secret   # skip secret, files only
#
# Requires: gh (authenticated), jq, git.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$HERE/templates/claude-review.yml"
OWNER="$(jq -r .owner "$HERE/projects.json")"
SET_SECRET=true
[[ "${1:-}" == "--no-secret" ]] && SET_SECRET=false

repos="$(jq -r '.tracks[].repo | select(. != "")' "$HERE/projects.json" | sort -u)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

for repo in $repos; do
  echo "==> $OWNER/$repo"
  dir="$work/$repo"
  if ! gh repo clone "$OWNER/$repo" "$dir" -- --depth 1 -q 2>/dev/null; then
    echo "    ! clone failed, skipping"; continue
  fi
  mkdir -p "$dir/.github/workflows"
  cp "$TEMPLATE" "$dir/.github/workflows/claude-review.yml"

  git -C "$dir" add .github/workflows/claude-review.yml
  if git -C "$dir" diff --cached --quiet; then
    echo "    = workflow already up to date"
  else
    git -C "$dir" -c user.name="Robert James" -c user.email="robertjam954@gmail.com" \
      commit -q -m "Add Claude auto code-review workflow"
    git -C "$dir" push -q
    echo "    + workflow pushed"
  fi

  if $SET_SECRET; then
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
      gh secret set ANTHROPIC_API_KEY -R "$OWNER/$repo" -b "$ANTHROPIC_API_KEY"
      echo "    + ANTHROPIC_API_KEY secret set"
    else
      echo "    ! ANTHROPIC_API_KEY not in env - set it later with:"
      echo "        gh secret set ANTHROPIC_API_KEY -R $OWNER/$repo"
    fi
  fi
done
echo "Done."
