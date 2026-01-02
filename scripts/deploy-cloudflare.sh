#!/bin/bash
set -e

cd "$(dirname "$0")/../cloudflare"

if ! command -v wrangler >/dev/null 2>&1; then
  echo "wrangler is required. Install with: npm install -g wrangler"
  exit 1
fi

wrangler deploy
