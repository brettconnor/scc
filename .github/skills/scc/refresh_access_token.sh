#!/usr/bin/env bash
# refresh_access_token.sh — Refresh the SCC API bearer token
# Usage: bash .github/skills/scc/refresh_access_token.sh
# Requires: curl, python3 (stdlib, for JSON parsing only)
#
# On success, prints the new access_token JSON response.
# Update SCC_API_KEY in hosts.sh with the returned access_token value.
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

for var in SCC_API_KEY SCC_API_KEY_ID SCC_REFRESH_KEY; do
    if [[ -z "${!var:-}" ]]; then
        echo "ERROR: ${var} not set in hosts.sh" >&2
        exit 1
    fi
done

BASE_URL="${SCC_URL:-https://api.security.cisco.com/v1/}"
BASE_URL="${BASE_URL%/}"

# Resolve org UUID from the API (SCC_ORG_ID in hosts.sh is the display name)
ORG_UUID=$(curl -s -X GET "${BASE_URL}/organizations" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${SCC_API_KEY}" \
    --max-time 15 \
    | python3 -c "import sys,json; orgs=json.load(sys.stdin).get('organizations',[]); print(orgs[0]['id'] if orgs else '')" 2>/dev/null) || true

if [[ -z "${ORG_UUID:-}" ]]; then
    echo "ERROR: Could not resolve org UUID from ${BASE_URL}/organizations" >&2
    exit 1
fi

URL="${BASE_URL}/organizations/${ORG_UUID}/apiKeys/${SCC_API_KEY_ID}/token"

_REFRESH_RAW=$(curl -s -w "\n%{http_code}" -X POST "${URL}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${SCC_API_KEY}" \
    -d "grant_type=refresh_token&refresh_token=${SCC_REFRESH_KEY}" \
    --max-time 15)
REFRESH_STATUS=$(printf '%s' "${_REFRESH_RAW}" | tail -n1)
REFRESH_BODY=$(printf '%s' "${_REFRESH_RAW}" | sed '$d')
unset _REFRESH_RAW

if [[ "${REFRESH_STATUS}" != "200" ]]; then
    echo "ERROR: Token refresh failed — HTTP ${REFRESH_STATUS}" >&2
    echo "${REFRESH_BODY}" | python3 -m json.tool >&2 2>/dev/null || echo "${REFRESH_BODY}" >&2
    exit 1
fi

echo "${REFRESH_BODY}" | python3 -m json.tool
