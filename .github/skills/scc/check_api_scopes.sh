#!/usr/bin/env bash
# check-api-scopes.sh — Diagnostic script to inspect API key scopes and permissions
# Usage: bash .github/skills/scc/check-api-scopes.sh
# Requires: curl, python3 (stdlib only)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
HOSTS_FILE="${REPO_ROOT}/hosts.sh"

# ── Load credentials ──────────────────────────────────────────────────────────
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

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          SCC API Key Scope & Permission Analyzer         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Decode JWT payload ────────────────────────────────────────────────────────
echo "Decoding API key JWT payload..."
echo ""

JWT_PAYLOAD=$(echo "${SCC_API_KEY}" | cut -d. -f2)
# Add padding if needed (no leading '=' separator)
JWT_PAYLOAD="${JWT_PAYLOAD}$(printf '%*s' $(( (4 - ${#JWT_PAYLOAD} % 4) % 4 )) | tr ' ' '=')"

DECODED=$(echo "${JWT_PAYLOAD}" | python3 -c "
import sys, base64, json
try:
    b64 = sys.stdin.read().strip()
    payload = json.loads(base64.urlsafe_b64decode(b64))
    print(json.dumps(payload, indent=2))
except Exception as e:
    print(f'ERROR: Failed to decode JWT: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1) || {
    echo "ERROR: Could not decode JWT token" >&2
    exit 1
}

echo "╭─ JWT Claims ─────────────────────────────────────────────╮"
echo "${DECODED}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for key in sorted(data.keys()):
    value = data[key]
    # Pretty-print lists
    if isinstance(value, list):
        if len(value) == 0:
            print(f'  {key}: []')
        elif len(value) <= 3:
            print(f'  {key}: {json.dumps(value)}')
        else:
            print(f'  {key}:')
            for item in value:
                print(f'    - {item}')
    elif isinstance(value, dict):
        print(f'  {key}: {json.dumps(value)}')
    else:
        print(f'  {key}: {value}')
"
echo "╰────────────────────────────────────────────────────────╯"
echo ""

# ── Analyze scopes ───────────────────────────────────────────────────────────
echo "╭─ Scope Analysis ─────────────────────────────────────────╮"

SCOPES=$(echo "${DECODED}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
scopes = data.get('scp', [])
if isinstance(scopes, str):
    # Sometimes it's a space-separated string
    scopes = scopes.split()
for s in scopes:
    print(s)
" 2>/dev/null || true)

if [[ -z "${SCOPES}" ]]; then
    echo "  ⚠ No scopes found in token"
else
    echo "  ✓ Scopes present:"
    echo ""
    while IFS= read -r scope; do
        if [[ -z "${scope}" ]]; then
            continue
        fi
        # Categorize scope
        case "${scope}" in
            *"mcp"* | *"platform_management"*)
                icon="🔌"
                category="MCP"
                ;;
            *"domain"* | *"object"*)
                icon="🔒"
                category="Security Objects"
                ;;
            *"policy"*)
                icon="📋"
                category="Policies"
                ;;
            *"device"* | *"network"*)
                icon="🖥️"
                category="Network/Devices"
                ;;
            *"user"* | *"group"* | *"role"* | *"identity"*)
                icon="👥"
                category="Identity"
                ;;
            *)
                icon="⚙️"
                category="Other"
                ;;
        esac
        printf "    %s %-20s %s\n" "${icon}" "${category}" "${scope}"
    done <<< "${SCOPES}"
fi
echo "╰────────────────────────────────────────────────────────╯"
echo ""

# ── Check endpoint access ─────────────────────────────────────────────────────
echo "╭─ Endpoint Accessibility ─────────────────────────────────╮"

# Initialize status variables
ORG_STATUS="000"
MCP_STATUS="000"
OBJECTS_STATUS="000"

# Test REST API organizations endpoint — single curl, split body and status
echo "  Testing: GET /organizations (REST API)..."
_ORG_RAW=$(curl -s -w "\n%{http_code}" -X GET "https://api.security.cisco.com/v1/organizations" \
    -H "Authorization: Bearer ${SCC_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time 10)
ORG_STATUS=$(printf '%s' "${_ORG_RAW}" | tail -n1)
ORG_RESP=$(printf '%s' "${_ORG_RAW}" | sed '$d')
unset _ORG_RAW
if [[ "${ORG_STATUS}" == "200" ]]; then
    echo "    ✓ 200 OK — Organizations endpoint accessible"
else
    echo "    ✗ HTTP ${ORG_STATUS} — Organizations endpoint returned error"
fi

# Test MCP endpoint
echo "  Testing: MCP initialize (JSON-RPC)..."
MCP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://mcp.security.cisco.com/mcp" \
    -H "Authorization: Bearer ${SCC_API_KEY}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"check-scopes","version":"1.0"}}}' \
    --max-time 10)
if [[ "${MCP_STATUS}" == "200" ]]; then
    echo "    ✓ 200 OK — MCP server accessible"
else
    echo "    ✗ HTTP ${MCP_STATUS} — MCP endpoint returned error"
fi

# Test objects endpoint (the one that requires specific scope)
echo "  Testing: GET /organizations/.../domains/global/objects (REST API)..."
ORG_UUID=$(echo "${ORG_RESP}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    org = data.get('organizations', [{}])[0]
    print(org.get('id', ''))
except:
    print('')
" 2>/dev/null || echo "")

if [[ -n "${ORG_UUID}" ]]; then
    OBJECTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "https://api.security.cisco.com/v1/organizations/${ORG_UUID}/domains/global/objects" \
        -H "Authorization: Bearer ${SCC_API_KEY}" \
        -H "Content-Type: application/json" \
        --max-time 10)
    if [[ "${OBJECTS_STATUS}" == "200" ]]; then
        echo "    ✓ 200 OK — Objects endpoint accessible"
    elif [[ "${OBJECTS_STATUS}" == "403" ]]; then
        echo "    ✗ 403 Forbidden — Insufficient scopes for objects endpoint"
        echo "      → API key needs 'domains:read' or 'objects:read' scope"
    else
        echo "    ✗ HTTP ${OBJECTS_STATUS} — Objects endpoint error"
    fi
else
    echo "    ⚠ Could not determine org UUID, skipping objects test"
fi

echo "╰────────────────────────────────────────────────────────╯"
echo ""

# ── Summary and recommendations ───────────────────────────────────────────────
echo "╭─ Summary ────────────────────────────────────────────────╮"
echo ""
echo "  Current API Key Capabilities:"
echo "    • MCP platform_management tools: $(echo "${SCOPES}" | grep -q 'mcp\|platform_management' && echo '✓ YES' || echo '✗ NO')"
echo "    • REST API read access: $(if [[ "${ORG_STATUS}" == "200" ]]; then echo "✓ YES"; else echo "✗ NO"; fi)"
echo "    • Security objects access: $(if [[ "${OBJECTS_STATUS}" == "200" ]]; then echo "✓ YES"; else echo "✗ NO (missing scope)"; fi)"
echo ""
echo "  To access security objects, ensure your API key has:"
echo "    • Scope: domains:read OR objects:read"
echo "    • Domain: /domains/global/objects"
echo ""
echo "╰────────────────────────────────────────────────────────╯"
