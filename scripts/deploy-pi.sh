#!/usr/bin/env bash
set -euo pipefail

# Deploy the Pi application to a remote host over SSH.
#
# Usage:
#   ./scripts/deploy-pi.sh <user@host> [--dest /opt/tesla-dashcam] [--venv .venv] [--install-service] [--restart-service]
#
# Environment overrides:
#   PI_HOST               Remote host (user@host). Used if the first arg is omitted.
#   PI_DEST               Remote destination directory. Default: /opt/tesla-dashcam
#   PI_VENV               Remote venv dir (absolute or relative to dest). Default: .venv
#   INSTALL_SERVICE=true  Run the remote install_service.sh after syncing.
#   RESTART_SERVICE=true  Restart the systemd service after deploy.
#
# Requirements on the remote host:
#   - SSH access with your key
#   - python3 and venv module available
#   - sudo access to create/manage the destination directory and systemd service

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_PI="$PROJECT_ROOT/pi"

HOST="${PI_HOST:-}"
DEST="${PI_DEST:-/opt/tesla-dashcam}"
VENV_NAME="${PI_VENV:-.venv}"
INSTALL_SERVICE="${INSTALL_SERVICE:-false}"
RESTART_SERVICE="${RESTART_SERVICE:-false}"
SERVICE_NAME="tesla-dashcam"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      DEST="$2"
      shift 2
      ;;
    --venv)
      VENV_NAME="$2"
      shift 2
      ;;
    --install-service)
      INSTALL_SERVICE=true
      shift
      ;;
    --restart-service)
      RESTART_SERVICE=true
      shift
      ;;
    *)
      if [[ -z "$HOST" ]]; then
        HOST="$1"
      else
        echo "Unknown argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$HOST" ]]; then
  echo "Usage: $0 <user@host> [--dest /opt/tesla-dashcam] [--venv .venv] [--install-service] [--restart-service]" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required locally" >&2
  exit 1
fi

echo "==> Deploying Pi app"
echo "Host: $HOST"
echo "Dest: $DEST"
echo "Venv: $VENV_NAME"
echo "Install service: $INSTALL_SERVICE"
echo "Restart service: $RESTART_SERVICE"

echo "==> Ensuring remote destination exists and ownership is set"
ssh "$HOST" "sudo mkdir -p '$DEST' && sudo chown -R \"\$(whoami)\" '$DEST'"

echo "==> Syncing files to remote"
rsync -az --delete \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude 'models/*.hef' \
  "$LOCAL_PI/" "$HOST:$DEST/"

echo "==> Setting up virtual environment and installing dependencies"
ssh "$HOST" "set -euo pipefail; \
  PYTHON_BIN=python3; \
  VENV_PATH='$DEST/$VENV_NAME'; \
  if ! command -v \"\$PYTHON_BIN\" >/dev/null 2>&1; then \
    echo 'python3 not found on remote host' >&2; exit 1; \
  fi; \
  \"\$PYTHON_BIN\" -m venv \"\$VENV_PATH\"; \
  source \"\$VENV_PATH/bin/activate\"; \
  pip install --upgrade pip; \
  pip install -r '$DEST/requirements.txt' \
"

if [[ "$INSTALL_SERVICE" == "true" ]]; then
  echo "==> Installing systemd service on remote"
  ssh "$HOST" "cd '$DEST' && sudo bash scripts/install_service.sh"
fi

if [[ "$RESTART_SERVICE" == "true" ]]; then
  echo "==> Restarting systemd service ($SERVICE_NAME)"
  ssh "$HOST" "sudo systemctl restart '$SERVICE_NAME'"
fi

echo "==> Deployment complete"
