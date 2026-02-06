#!/usr/bin/env bash
# make-apt-repo.sh - Generate a minimal apt repo from the latest pf-runner .deb
# Usage:
#   CODENAME=bookworm REPO_DIR=apt-repo ./make-apt-repo.sh
# Env vars:
#   CODENAME   - debian/ubuntu codename (default: bookworm)
#   REPO_DIR   - output repo root (default: apt-repo)
#   DEB_PATH   - path to .deb (default: build-packages/deb/pf-runner_latest.deb)
#   GPG_KEY    - optional GPG key id/email to sign Release (clearsign + detached)
set -euo pipefail

CODENAME=${CODENAME:-bookworm}
REPO_DIR=${REPO_DIR:-apt-repo}
DEB_PATH=${DEB_PATH:-build-packages/deb/pf-runner_latest.deb}

if [[ ! -f "$DEB_PATH" ]]; then
  echo "[ERROR] .deb not found at $DEB_PATH. Build it first." >&2
  exit 1
fi

if ! command -v dpkg-scanpackages >/dev/null 2>&1; then
  echo "[ERROR] dpkg-scanpackages not installed (apt-get install dpkg-dev)." >&2
  exit 1
fi

POOL="$REPO_DIR/pool/main/p/pf-runner"
DIST="$REPO_DIR/dists/$CODENAME"
BIN="$DIST/main/binary-amd64"

echo "[INFO] Preparing repo directories..."
mkdir -p "$POOL" "$BIN"

echo "[INFO] Copying .deb..."
cp "$DEB_PATH" "$POOL/"

echo "[INFO] Generating Packages index..."
dpkg-scanpackages "$POOL" /dev/null > "$BIN/Packages"
gzip -kf "$BIN/Packages"

echo "[INFO] Writing Release..."
cat > "$DIST/Release" <<EOF
Origin: pf-runner
Label: pf-runner
Suite: $CODENAME
Codename: $CODENAME
Architectures: amd64
Components: main
Date: $(date -Ru)
Description: pf-runner apt repository
EOF

if [[ -n "${GPG_KEY:-}" ]]; then
  echo "[INFO] Signing Release with GPG key $GPG_KEY..."
  gpg --default-key "$GPG_KEY" --clearsign -o "$DIST/InRelease" "$DIST/Release"
  gpg --default-key "$GPG_KEY" -abs -o "$DIST/Release.gpg" "$DIST/Release"
else
  echo "[WARN] GPG_KEY not set; repo left unsigned."
fi

echo "[OK] Repo ready at $REPO_DIR"
echo "Add to apt sources (example):"
echo "  echo 'deb [trusted=yes] https://your.host/$REPO_DIR $CODENAME main' | sudo tee /etc/apt/sources.list.d/pf-runner.list"
echo "Prefer signed: upload $REPO_DIR, distribute the pubkey, and drop 'trusted=yes'."
