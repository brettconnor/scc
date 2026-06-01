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

# ---------------------------------------------------------------------------
# Virtual environment setup — uv preferred, stdlib venv fallback
# ---------------------------------------------------------------------------
if command -v uv >/dev/null 2>&1; then
  USE_UV=1
  echo "Python env: uv detected"
else
  USE_UV=0
  echo "Python env: uv not found, using stdlib venv"
fi

if [[ ! -d ".venv" ]]; then
  echo "Creating .venv..."
  if (( USE_UV )); then
    uv venv .venv
  else
    python3 -m venv .venv
  fi
fi

PYTHON="${REPO_ROOT}/.venv/bin/python3"
echo "Python: ${PYTHON}"

echo "Installing scc-sdk into .venv..."
if (( USE_UV )); then
  if ! uv pip install --python "${PYTHON}" -e ./scc-sdk; then
    echo "uv pip install failed. Falling back to pip..."
    USE_UV=0
  fi
fi
if (( USE_UV == 0 )); then
  PIP="${REPO_ROOT}/.venv/bin/pip"
  if ! "${PIP}" install -e ./scc-sdk; then
    echo "Default index install failed. Trying public PyPI fallback..."
    if ! PIP_INDEX_URL="${PIP_INDEX_URL_FALLBACK:-https://pypi.org/simple}" \
        "${PIP}" install -e ./scc-sdk; then
      echo "ERROR: failed to install scc-sdk"
      echo "Remediation: verify pip index configuration or internal mirror availability"
      exit 1
    fi
  fi
fi

# Install any additional scc-sdk requirements if present
if [[ -f "scc-sdk/requirements.txt" ]]; then
  echo "Installing scc-sdk/requirements.txt..."
  if (( USE_UV )); then
    uv pip install --python "${PYTHON}" -r scc-sdk/requirements.txt
  else
    "${REPO_ROOT}/.venv/bin/pip" install -r scc-sdk/requirements.txt
  fi
fi
# ---------------------------------------------------------------------------

if [[ ! -f "hosts.sh" ]]; then
  echo "ERROR: hosts.sh not found at repo root"
  echo "Remediation: cp hosts.sh.example hosts.sh && edit with real values"
  exit 1
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
"${PYTHON}" ".github/skills/scc_hybrid/scc_hybrid_context.py"

echo "Bootstrap complete: hybrid context is ready"
