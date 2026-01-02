#!/usr/bin/env bash
set -euo pipefail

# Deploy the Cloudflare Worker using wrangler.
#
# Usage:
#   ./scripts/deploy-cloudflare.sh [--env <name>] [--skip-install] [--skip-checks]
#
# Defaults:
#   ENV=production (wrangler env name)
#   Installs dependencies, runs lint/typecheck/tests, then wrangler deploy.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CF_DIR="$ROOT_DIR/cloudflare"

ENV_NAME="production"
SKIP_INSTALL=false
SKIP_CHECKS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENV_NAME="$2"
      shift 2
      ;;
    --skip-install)
      SKIP_INSTALL=true
      shift
      ;;
    --skip-checks)
      SKIP_CHECKS=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v wrangler >/dev/null 2>&1; then
  echo "wrangler is required. Install with: npm install -g wrangler" >&2
  exit 1
fi

cd "$CF_DIR"

if [[ "$SKIP_INSTALL" == "false" ]]; then
  echo "==> Installing dependencies"
  npm install
fi

if [[ "$SKIP_CHECKS" == "false" ]]; then
  echo "==> Running lint/typecheck/tests"
  npm run check
  npm test
fi

echo "==> Deploying with wrangler (env: $ENV_NAME)"
wrangler deploy --env "$ENV_NAME"

echo "==> Cloudflare deploy complete"
