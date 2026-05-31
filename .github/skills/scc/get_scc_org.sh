#!/usr/bin/env bash
# get_scc_org.sh — List SCC organizations for the authenticated user
# Usage: bash .github/skills/scc/get_scc_org.sh
# Requires: curl, python3 (stdlib, for JSON pretty-print only)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
HOSTS_FILE="${REPO_ROOT}/hosts.sh"

if [[ ! -f "${HOSTS_FILE}" ]]; then
    echo "ERROR: hosts.sh not found at ${HOSTS_FILE}" >&2
    exit 1
fi
# shellcheck source=/dev/null
source "${HOSTS_FILE}"

if [[ -z "${SCC_API_KEY:-}" ]]; then
    echo "ERROR: SCC_API_KEY not set in hosts.sh" >&2
    exit 1
fi

BASE_URL="${SCC_URL:-https://api.security.cisco.com/v1/}"
BASE_URL="${BASE_URL%/}"    # strip trailing slash

curl -s -X GET "${BASE_URL}/organizations" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${SCC_API_KEY}" \
    --max-time 15 \
    | python3 -m json.tool
