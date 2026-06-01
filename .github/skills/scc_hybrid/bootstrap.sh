#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

cd "${REPO_ROOT}"

echo "SCC Hybrid bootstrap"
echo "===================="
echo "Repo: ${REPO_ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH"
  exit 1
fi

if [[ ! -f "hosts.sh" ]]; then
  echo "ERROR: hosts.sh not found at repo root"
  echo "Remediation: cp hosts.sh.example hosts.sh && edit with real values"
  exit 1
fi

# Ensure scc-sdk dependency is available before importing hybrid context.
if ! python3 -c 'import requests' >/dev/null 2>&1; then
  echo "Dependency missing: requests"
  echo "Installing scc-sdk requirements from default index..."
  if ! python3 -m pip install -r "scc-sdk/requirements.txt"; then
    echo "Default index install failed. Trying public PyPI fallback..."
    if ! PIP_INDEX_URL="${PIP_INDEX_URL_FALLBACK:-https://pypi.org/simple}" \
      python3 -m pip install -r "scc-sdk/requirements.txt"; then
      echo "ERROR: failed to install scc-sdk requirements"
      echo "Remediation: verify pip index configuration or internal mirror availability"
      exit 1
    fi
  fi
fi

echo "Exporting SCC credentials from hosts.sh"
set -a
# shellcheck disable=SC1091
source "hosts.sh"
set +a

required_vars=(SCC_API_KEY SCC_ORG_ID SCC_ORG_UUID SCC_API_KEY_ID SCC_URL)
missing=()
for name in "${required_vars[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    missing+=("${name}")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "ERROR: missing required environment variables: ${missing[*]}"
  exit 1
fi

echo "Running SCC hybrid smoke test"
python3 ".github/skills/scc_hybrid/scc_hybrid_context.py"

echo "Bootstrap complete: hybrid context is ready"
