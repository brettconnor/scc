#!/usr/bin/env bash
# check_fmc_api.sh - Test FMC API connectivity and authentication
#
# Usage: bash .github/skills/scc_fm/check_fmc_api.sh
#
# Verifies:
# - hosts.sh credentials are loaded
# - FMC API authentication works
# - Device inventory endpoint is accessible
# - Returns basic API health information

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "FMC API Connectivity Test"
echo "================================================"
echo ""

# Find and source hosts.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HOSTS_FILE="$REPO_ROOT/hosts.sh"

if [[ ! -f "$HOSTS_FILE" ]]; then
    echo -e "${RED}✗ hosts.sh not found at: $HOSTS_FILE${NC}"
    echo "RESULT: FAIL"
    exit 1
fi

# Source credentials
# shellcheck disable=SC1090
source "$HOSTS_FILE"

# Check required variables
if [[ -z "${SCC_FMC_API_KEY:-}" ]]; then
    echo -e "${RED}✗ SCC_FMC_API_KEY not set in hosts.sh${NC}"
    echo "RESULT: FAIL"
    exit 1
fi

if [[ -z "${SCC_EDGE_URL:-}" ]]; then
    echo -e "${RED}✗ SCC_EDGE_URL not set in hosts.sh${NC}"
    echo "RESULT: FAIL"
    exit 1
fi

echo -e "${GREEN}✓ Credentials loaded from hosts.sh${NC}"
echo "  Endpoint: $SCC_EDGE_URL"
echo "  Token: ${SCC_FMC_API_KEY:0:10}...${SCC_FMC_API_KEY: -4}"
echo ""

# Test 1: Device inventory endpoint
echo "Test 1: Device Inventory Access"
echo "  GET $SCC_EDGE_URL/v1/inventory/devices?limit=1"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET \
    "$SCC_EDGE_URL/v1/inventory/devices?limit=1" \
    -H "Authorization: Bearer $SCC_FMC_API_KEY" \
    -H "Accept: application/json")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" == "200" ]]; then
    echo -e "${GREEN}✓ Authentication successful (HTTP 200)${NC}"
    
    # Parse device count
    DEVICE_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('count', 0))")
    echo "  Device Count: $DEVICE_COUNT"
    
elif [[ "$HTTP_CODE" == "401" ]]; then
    echo -e "${RED}✗ Authentication failed (HTTP 401)${NC}"
    echo "  Check SCC_FMC_API_KEY in hosts.sh"
    echo "  Token may be expired or invalid"
    echo "RESULT: FAIL"
    exit 1
elif [[ "$HTTP_CODE" == "404" ]]; then
    echo -e "${RED}✗ Endpoint not found (HTTP 404)${NC}"
    echo "  Check SCC_EDGE_URL in hosts.sh"
    echo "  Verify you're using the FMC API endpoint"
    echo "RESULT: FAIL"
    exit 1
else
    echo -e "${RED}✗ Unexpected response (HTTP $HTTP_CODE)${NC}"
    echo "  Response: $BODY"
    echo "RESULT: FAIL"
    exit 1
fi

echo ""

# Test 2: Check managers endpoint for cdFMC
echo "Test 2: Manager Access (cdFMC Discovery)"
echo "  GET $SCC_EDGE_URL/v1/inventory/managers?limit=1"

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET \
    "$SCC_EDGE_URL/v1/inventory/managers?limit=1" \
    -H "Authorization: Bearer $SCC_FMC_API_KEY" \
    -H "Accept: application/json")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [[ "$HTTP_CODE" == "200" ]]; then
    echo -e "${GREEN}✓ Manager endpoint accessible${NC}"
else
    echo -e "${YELLOW}⚠ Manager endpoint returned HTTP $HTTP_CODE${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}RESULT: PASS${NC}"
echo "================================================"
echo ""
echo "FMC API is accessible and authentication is working."
echo ""
echo "Next steps:"
echo "  - List devices: bash .github/skills/scc_fm/get_devices.sh"
echo "  - Find cdFMC:   bash .github/skills/scc_fm/get_cdfmc.sh"
echo "  - Use SDK:      python3 scripts/example_inventory.py"
