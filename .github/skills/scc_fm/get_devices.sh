#!/usr/bin/env bash
# get_devices.sh - Quick device inventory query
#
# Usage: bash .github/skills/scc_fm/get_devices.sh
#
# Returns device count and basic information without requiring SDK

set -euo pipefail

# Find and source hosts.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HOSTS_FILE="$REPO_ROOT/hosts.sh"

if [[ ! -f "$HOSTS_FILE" ]]; then
    echo "✗ hosts.sh not found at: $HOSTS_FILE"
    exit 1
fi

# Source credentials
# shellcheck disable=SC1090
source "$HOSTS_FILE"

# Check required variables
if [[ -z "${SCC_FMC_API_KEY:-}" ]] || [[ -z "${SCC_EDGE_URL:-}" ]]; then
    echo "✗ SCC_FMC_API_KEY or SCC_EDGE_URL not set in hosts.sh"
    exit 1
fi

echo "Querying device inventory..."
echo ""

# Query devices
RESPONSE=$(curl -s \
    -X GET \
    "$SCC_EDGE_URL/v1/inventory/devices" \
    -H "Authorization: Bearer $SCC_FMC_API_KEY" \
    -H "Accept: application/json")

# Check if response is valid JSON
if ! echo "$RESPONSE" | python3 -m json.tool >/dev/null 2>&1; then
    echo "✗ Invalid JSON response from API"
    echo "Response: $RESPONSE"
    exit 1
fi

# Parse and display results
python3 -c "
import json

data = json.loads('''$RESPONSE''')

print('=' * 60)
print('Device Inventory Summary')
print('=' * 60)
print(f\"Total Devices: {data.get('count', 0)}\")
print(f\"Limit: {data.get('limit', 50)}\")
print(f\"Offset: {data.get('offset', 0)}\")
print('=' * 60)
print('')

items = data.get('items', [])

if not items:
    print('No devices found.')
else:
    for device in items:
        print(f\"Device: {device.get('name', 'N/A')}\")
        print(f\"  UID: {device.get('uid', 'N/A')}\")
        print(f\"  Type: {device.get('deviceType', 'N/A')}\")
        print(f\"  Address: {device.get('address', 'N/A')}\")
        print(f\"  State: {device.get('connectivityState', 'N/A')}\")
        print(f\"  Config: {device.get('configState', 'N/A')}\")
        print('')
"
