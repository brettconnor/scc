#!/usr/bin/env bash
# check_mcp.sh — SCC MCP connectivity test and tool inventory report
# Usage: bash .github/skills/scc/check_mcp.sh
# Requires: curl, python3 (stdlib only)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
HOSTS_FILE="${REPO_ROOT}/hosts.sh"
MCP_URL="${MCP_SERVER_URL:-https://mcp.security.cisco.com/mcp}"

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

TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║        SCC MCP Connectivity & Tool Inventory             ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo "  Timestamp : ${TIMESTAMP}"
echo "  MCP URL   : ${MCP_URL}"
echo "  Org       : ${SCC_ORG_ID:-<not set>}"
echo "  User      : ${SCC_USERNAME:-<not set>}"
echo "  Key ID    : ${SCC_API_KEY_ID:-<not set>}"
echo ""

# ── Step 1: Initialize ────────────────────────────────────────────────────────
echo "── Step 1: Initialize MCP session ──"
INIT_HTTP=$(curl -si -X POST "${MCP_URL}" \
    -H "Authorization: Bearer ${SCC_API_KEY}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"check_mcp","version":"1.0"}}}' \
    --max-time 15 2>&1) || true

HTTP_STATUS=$(echo "${INIT_HTTP}" | grep -m1 "^HTTP/" | awk '{print $2}') || true
SESSION_ID=$(echo "${INIT_HTTP}" | grep -i "^mcp-session-id:" | awk '{print $2}' | tr -d '\r') || true
INIT_DATA=$(echo "${INIT_HTTP}" | grep '^data:' | sed 's/^data: //') || true

if [[ "${HTTP_STATUS}" != "200" ]]; then
    echo "  FAIL — HTTP ${HTTP_STATUS:-<no response>}"
    echo ""
    echo "  Raw response:"
    echo "${INIT_HTTP}" | head -20
    exit 1
fi

SERVER_NAME=$(echo "${INIT_DATA}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('serverInfo',{}).get('name','unknown'))" 2>/dev/null || echo "unknown")
SERVER_VER=$(echo "${INIT_DATA}"  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('serverInfo',{}).get('version','unknown'))" 2>/dev/null || echo "unknown")
PROTO_VER=$(echo "${INIT_DATA}"   | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result',{}).get('protocolVersion','unknown'))" 2>/dev/null || echo "unknown")

echo "  OK"
echo "  Server    : ${SERVER_NAME} v${SERVER_VER}"
echo "  Protocol  : ${PROTO_VER}"
[[ -n "${SESSION_ID}" ]] && echo "  Session   : ${SESSION_ID}" || echo "  Session   : (stateless — server does not require session ID)"
echo ""

# ── Step 2: tools/list ────────────────────────────────────────────────────────
echo "── Step 2: Retrieve tool inventory ──"
TOOLS_CURL_ARGS=(
    -s -X POST "${MCP_URL}"
    -H "Authorization: Bearer ${SCC_API_KEY}"
    -H "Content-Type: application/json"
    -H "Accept: application/json, text/event-stream"
)
[[ -n "${SESSION_ID}" ]] && TOOLS_CURL_ARGS+=(-H "mcp-session-id: ${SESSION_ID}")
TOOLS_CURL_ARGS+=(-d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')

TOOLS_RESP=$(curl "${TOOLS_CURL_ARGS[@]}" --max-time 15 2>/dev/null | grep '^data:' | sed 's/^data: //') || true
TOOLS_RESP="${TOOLS_RESP:-}"

if [[ -z "${TOOLS_RESP}" ]]; then
    echo "  FAIL — Empty response from tools/list"
    exit 1
fi

TOOL_COUNT=$(echo "${TOOLS_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('result',{}).get('tools',[])))" 2>/dev/null || echo "0")
echo "  OK — ${TOOL_COUNT} tools discovered"
echo ""

# ── Step 3: Tool inventory report ─────────────────────────────────────────────
echo "── Step 3: Tool inventory ──"
echo "${TOOLS_RESP}" | python3 -c "
import sys, json, textwrap

data = json.load(sys.stdin)
tools = data.get('result', {}).get('tools', [])

groups = {}
for t in tools:
    prefix = t['name'].rsplit('_', maxsplit=1)[0] if '_' in t['name'] else 'other'
    # group by first two underscore segments
    parts = t['name'].split('_')
    group = '_'.join(parts[:2]) if len(parts) >= 2 else parts[0]
    groups.setdefault(group, []).append(t)

for grp, items in sorted(groups.items()):
    print(f'  [{grp}]')
    for t in items:
        desc = t.get('description', '').split('\n')[0][:72]
        print(f'    {t[\"name\"]:<55} {desc}')
    print()
"

# ── Summary ───────────────────────────────────────────────────────────────────
echo "── Summary ──"
echo "  Connectivity : PASS"
echo "  Tools found  : ${TOOL_COUNT}"
echo "  Completed    : $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo ""
echo "RESULT: PASS"
