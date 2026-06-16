#!/usr/bin/env bash
# Example: Network Object Creation Workflow
# 
# This demonstrates how to use the FMC script template to create
# multiple network objects from a list.
#
# Usage:
#   bash .github/skills/scc_fm_codegen/example_workflow.sh
#
# This is an EXAMPLE - customize the template for your use case.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

cd "${REPO_ROOT}"

# Preflight checks
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found"
  exit 1
fi

if [[ ! -f "hosts.sh" ]]; then
  echo "ERROR: hosts.sh not found"
  exit 1
fi

if [[ ! -d "scc-fm-sdk/scc_firewall_manager_sdk" ]]; then
  echo "ERROR: FMC SDK not installed"
  exit 1
fi

# Load environment
set -a
source "hosts.sh"
set +a

# Execute workflow
python3 << 'PYTHON_EOF'

import sys
sys.path.insert(0, '/home/wolfy/scc/scc-fm-sdk')

from scc_firewall_manager_sdk import ApiClient, Configuration
from scc_firewall_manager_sdk.api.inventory_api import InventoryApi
import os

print("\n" + "=" * 80)
print("Example Workflow: Network Object Creation")
print("=" * 80 + "\n")

# Setup
api_key = os.getenv('SCC_FMC_API_KEY')
base_url = os.getenv('SCC_EDGE_URL')

config = Configuration(host=base_url, access_token=api_key)
client = ApiClient(configuration=config)

# Example: Query devices first
inventory_api = InventoryApi(client)
devices = inventory_api.get_devices()

print(f"Discovered {devices.count} devices:")
for device in devices.items:
    print(f"  - {device.name} ({device.device_type})")

print("\n" + "=" * 80)
print("Network Object Creation")
print("=" * 80)
print("\nThis is where you would:")
print("  1. Read network definitions from CSV/YAML")
print("  2. Validate network syntax (CIDR, etc.)")
print("  3. Check for existing objects (avoid duplicates)")
print("  4. Create network objects via ObjectManagementApi")
print("  5. Verify creation with GET requests")
print("  6. Generate audit report with timestamps and UIDs")
print()
print("See SKILL.md for complete patterns and examples.")
print()

print("=" * 80)
print("✓ Example workflow completed")
print("=" * 80 + "\n")

PYTHON_EOF

echo "✓ Example completed successfully"
