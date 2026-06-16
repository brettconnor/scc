#!/usr/bin/env bash
# get_cdfmc.sh - Discover cloud-delivered FMC (cdFMC) instance
#
# Usage: bash .github/skills/scc_fm/get_cdfmc.sh
#
# Returns cdFMC UID and domain UUID if present in the tenant

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

echo "Discovering cdFMC instance..."
echo ""

# Query for CDFMC device type
RESPONSE=$(curl -s \
    -X GET \
    "$SCC_EDGE_URL/v1/inventory/managers?q=deviceType:CDFMC" \
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
print('Cloud-Delivered FMC (cdFMC) Discovery')
print('=' * 60)

items = data.get('items', [])

if not items:
    print('No cdFMC found in this tenant.')
    print('')
    print('This is normal if you are using:')
    print('  - On-premises FMC')
    print('  - CDO without cdFMC')
    print('  - Device-local management')
else:
    for manager in items:
        print(f\"cdFMC Name: {manager.get('name', 'N/A')}\")
        print(f\"  UID: {manager.get('uid', 'N/A')}\")
        print(f\"  Device Type: {manager.get('deviceType', 'N/A')}\")
        print(f\"  State: {manager.get('state', 'N/A')}\")
        
        # Extract domain UUID if available (for cdFMC API operations)
        if 'specificUid' in manager:
            print(f\"  Domain UUID: {manager.get('specificUid', 'N/A')}\")
        
        print('')
        print('Use these values for cdFMC-specific API operations:')
        print(f\"  Manager UID: {manager.get('uid', 'N/A')}\")
        if 'specificUid' in manager:
            print(f\"  Domain UUID: {manager.get('specificUid', 'N/A')}\")

print('=' * 60)
"
