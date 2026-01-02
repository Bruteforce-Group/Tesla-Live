#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Syncing Pi application to device..."
# TODO: implement rsync/ssh deployment to Raspberry Pi 5
echo "Project root: $PROJECT_ROOT"
