#!/bin/bash
# FMC Hybrid Context Bootstrap
# One-command preflight: SDK check, hosts.sh export, and smoke test

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== FMC Hybrid Context Bootstrap ==="
echo

# ---------------------------------------------------------------------------
# 1. Check FMC SDK Installation
# ---------------------------------------------------------------------------

SDK_PATH="/home/wolfy/scc/scc-fm-sdk"
SDK_MODULE="$SDK_PATH/scc_firewall_manager_sdk"

echo -n "Checking FMC SDK installation... "
if [ ! -d "$SDK_PATH" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "FMC SDK not found at $SDK_PATH"
    echo
    echo "Install with:"
    echo "  mkdir -p $SDK_PATH"
    echo "  pip install --target $SDK_PATH scc-firewall-manager-sdk"
    exit 1
fi

if [ ! -d "$SDK_MODULE" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "SDK module not found at $SDK_MODULE"
    echo "Reinstall SDK or check installation path"
    exit 1
fi

echo -e "${GREEN}OK${NC}"

# ---------------------------------------------------------------------------
# 2. Check hosts.sh
# ---------------------------------------------------------------------------

HOSTS_FILE="hosts.sh"
echo -n "Checking hosts.sh... "
if [ ! -f "$HOSTS_FILE" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "hosts.sh not found in current directory"
    echo "Expected location: $(pwd)/hosts.sh"
    exit 1
fi

echo -e "${GREEN}OK${NC}"

# ---------------------------------------------------------------------------
# 3. Validate hosts.sh syntax
# ---------------------------------------------------------------------------

echo -n "Validating hosts.sh syntax... "
if ! bash -n "$HOSTS_FILE" 2>/dev/null; then
    echo -e "${RED}FAIL${NC}"
    echo "hosts.sh has syntax errors"
    bash -n "$HOSTS_FILE"
    exit 1
fi

echo -e "${GREEN}OK${NC}"

# ---------------------------------------------------------------------------
# 4. Export environment variables
# ---------------------------------------------------------------------------

echo -n "Loading environment from hosts.sh... "
set -a
# shellcheck disable=SC1091
source "$HOSTS_FILE"
set +a
echo -e "${GREEN}OK${NC}"

# ---------------------------------------------------------------------------
# 5. Verify required environment variables
# ---------------------------------------------------------------------------

echo -n "Checking SCC_FMC_API_KEY... "
if [ -z "${SCC_FMC_API_KEY:-}" ]; then
    echo -e "${RED}MISSING${NC}"
    echo "SCC_FMC_API_KEY not set in hosts.sh"
    exit 1
fi
echo -e "${GREEN}SET${NC}"

echo -n "Checking SCC_EDGE_URL... "
if [ -z "${SCC_EDGE_URL:-}" ]; then
    echo -e "${RED}MISSING${NC}"
    echo "SCC_EDGE_URL not set in hosts.sh"
    exit 1
fi
echo -e "${GREEN}SET${NC} ($SCC_EDGE_URL)"

# ---------------------------------------------------------------------------
# 6. Check Python 3
# ---------------------------------------------------------------------------

echo -n "Checking Python 3... "
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}FAIL${NC}"
    echo "python3 not found in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}OK${NC} ($PYTHON_VERSION)"

# ---------------------------------------------------------------------------
# 7. Run smoke test
# ---------------------------------------------------------------------------

echo
echo "Running smoke test..."
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! python3 "$SCRIPT_DIR/fmc_hybrid_context.py"; then
    echo
    echo -e "${RED}✗ Smoke test failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Bootstrap complete${NC}"
echo
echo "FMC Hybrid Context is ready to use."
echo
echo "Example usage:"
echo "  set -a; source hosts.sh; set +a && python3 << 'EOF'"
echo "  import sys"
echo "  sys.path.insert(0, '.github/skills/scc_fm_hybrid')"
echo "  from fmc_hybrid_context import FMCHybridContext"
echo "  "
echo "  with FMCHybridContext() as ctx:"
echo "      devices = ctx.inventory.get_devices()"
echo "      print(f'Found {devices.count} devices')"
echo "  EOF"
echo
