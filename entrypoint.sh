#!/bin/bash
set -e

DATA_DIR="/app/data"
GITHUB_REPO="${GITHUB_REPO:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# --- Phase 1: Pull latest data from GitHub ---
if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_REPO" ]; then
  REMOTE_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"

  # Configure git safe directory (container user has no home dir)
  git config --global safe.directory "$DATA_DIR" 2>/dev/null || true

  if [ -d "$DATA_DIR/.git" ]; then
    # Existing repo: pull latest from GitHub
    echo "github-sync: pulling latest data from GitHub"
    cd "$DATA_DIR"
    git remote set-url origin "$REMOTE_URL" 2>/dev/null || git remote add origin "$REMOTE_URL"
    git fetch origin main --quiet
    git reset --hard origin/main
    cd /app
    echo "github-sync: data updated from GitHub"
  else
    # Fresh volume: sparse-clone just the data/ directory
    echo "github-sync: cloning data from GitHub (first run)"
    TMPDIR=$(mktemp -d)
    git clone --depth 1 --filter=blob:none --sparse "$REMOTE_URL" "$TMPDIR"
    cd "$TMPDIR"
    git sparse-checkout set data
    cp -a data/. "$DATA_DIR/"
    cd /app
    rm -rf "$TMPDIR"

    # Initialize as a standalone git repo so json_store.py works
    cd "$DATA_DIR"
    git init
    git add .
    git commit -m "Initial sync from GitHub"
    git remote add origin "$REMOTE_URL"
    cd /app
    echo "github-sync: initial clone complete"
  fi
else
  echo "github-sync: skipped (GITHUB_TOKEN or GITHUB_REPO not set)"
fi

# --- Phase 1b: Flatten data/ to the top level ---
# The data dir tracks the WHOLE repo (origin = the full project), so a
# `git reset --hard origin/main` lays the tree out as the repo root, leaving the
# JSON the server reads ($DATA_DIR/*.json) under $DATA_DIR/data/. Without this
# step the top-level files are missing after a reset and Phase 2 backfills them
# with the image's baked defaults, so GitHub data updates never take effect and
# a stale snapshot is served. Lift data/*.json up so the GitHub copy wins.
if [ -d "$DATA_DIR/data" ]; then
  cp -a "$DATA_DIR/data/." "$DATA_DIR/" 2>/dev/null && \
    echo "data-sync: flattened data/ to $DATA_DIR top level" || \
    echo "data-sync: flatten skipped (non-fatal)"
fi

# --- Phase 2: Fill in any new defaults not yet on GitHub ---
for f in /app/data-defaults/*.json; do
  name="$(basename "$f")"
  if [ ! -f "$DATA_DIR/$name" ]; then
    cp "$f" "$DATA_DIR/$name"
    echo "data-sync: copied $name"
  fi
done

# If the data dir is a Git repo, commit any new defaults.
if [ -d "$DATA_DIR/.git" ]; then
  cd "$DATA_DIR"
  git add -A
  git diff --cached --quiet || git commit -m "data-sync: add new default files"
  cd /app
fi

exec python src/server.py
