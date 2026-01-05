#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git config core.hooksPath "${repo_root}/.githooks"

echo "Configured git hooks path to ${repo_root}/.githooks"
