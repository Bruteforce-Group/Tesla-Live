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
SSH_OPTS=()
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
    --ssh-opts)
      SSH_OPTS+=("$2")
      shift 2
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
echo "SSH opts: ${SSH_OPTS[*]:-(none)}"

echo "==> Ensuring remote destination exists and ownership is set"
ssh "${SSH_OPTS[@]}" "$HOST" "sudo rm -rf '$DEST' && sudo mkdir -p '$DEST' && sudo chown -R \"\$(whoami)\" '$DEST'"

echo "==> Syncing files to remote (rsync if available, otherwise tar)"
if ssh "${SSH_OPTS[@]}" "$HOST" "command -v rsync >/dev/null 2>&1"; then
  rsync -az --delete \
    --exclude '.venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'models/*.hef' \
    "$LOCAL_PI/" "$HOST:$DEST/"
else
  echo "Remote rsync not found; using tar fallback"
  (cd "$LOCAL_PI" && tar -czf - \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='models/*.hef' \
    .) | ssh "${SSH_OPTS[@]}" "$HOST" "tar -xzf - -C '$DEST'"
fi

GET_PIP_LOCAL="/tmp/get-pip.py"
if [[ ! -f "$GET_PIP_LOCAL" ]]; then
  echo "==> Downloading get-pip.py locally"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://bootstrap.pypa.io/get-pip.py -o "$GET_PIP_LOCAL"
  else
    python3 - <<'PYCODE'
import urllib.request
url = "https://bootstrap.pypa.io/get-pip.py"
urllib.request.urlretrieve(url, "/tmp/get-pip.py")
PYCODE
  fi
fi

echo "==> Copying get-pip.py to remote /tmp"
scp "${SSH_OPTS[@]}" "$GET_PIP_LOCAL" "$HOST:/tmp/get-pip.py"

echo "==> Setting up environment and installing dependencies"
ssh "${SSH_OPTS[@]}" "$HOST" "set -euo pipefail; \
  PYTHON_BIN=python3; \
  VENV_PATH='$DEST/$VENV_NAME'; \
  if ! command -v \"\$PYTHON_BIN\" >/dev/null 2>&1; then \
    echo 'python3 not found on remote host' >&2; exit 1; \
  fi; \
  if \"\$PYTHON_BIN\" -m venv --without-pip \"\$VENV_PATH\" 2>/dev/null; then \
    echo 'Created venv without pip; bootstrapping pip inside venv'; \
    \"\$VENV_PATH/bin/python3\" /tmp/get-pip.py; \
    source \"\$VENV_PATH/bin/activate\"; \
    pip install --upgrade pip; \
    pip install -r '$DEST/requirements.txt'; \
    echo 'Installed dependencies in virtualenv'; \
  else \
    echo 'venv creation failed; falling back to system install (break-system-packages)'; \
    if ! \"\$PYTHON_BIN\" -m pip --version >/dev/null 2>&1; then \
      echo 'pip not present; bootstrapping via get-pip.py'; \
      \"\$PYTHON_BIN\" /tmp/get-pip.py --user --break-system-packages || \"\$PYTHON_BIN\" /tmp/get-pip.py --user; \
      rm -f /tmp/get-pip.py; \
    fi; \
    \"\$PYTHON_BIN\" -m pip install --break-system-packages --upgrade pip || \"\$PYTHON_BIN\" -m pip install --user --upgrade pip; \
    \"\$PYTHON_BIN\" -m pip install --break-system-packages -r '$DEST/requirements.txt' || \"\$PYTHON_BIN\" -m pip install --user -r '$DEST/requirements.txt'; \
  fi \
"

if [[ "$INSTALL_SERVICE" == "true" ]]; then
  echo "==> Installing systemd service on remote"
  ssh "${SSH_OPTS[@]}" "$HOST" "cd '$DEST' && APP_DIR='$DEST' sudo bash scripts/install_service.sh"
fi

if [[ "$RESTART_SERVICE" == "true" ]]; then
  echo "==> Restarting systemd service ($SERVICE_NAME)"
  ssh "${SSH_OPTS[@]}" "$HOST" "sudo systemctl restart '$SERVICE_NAME'"
fi

echo "==> Deployment complete"
