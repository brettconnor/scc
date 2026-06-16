#!/usr/bin/env bash
# FMC SDK Script Template
# 
# Usage: Copy this file and customize the Python section for your workflow.
# 
# DO NOT modify this template directly. Instead:
#   1. cp script_template.sh my_fmc_workflow.sh
#   2. Edit the PYTHON CODE SECTION (marked below)
#   3. Run: bash my_fmc_workflow.sh
# 
# Why this template exists:
#   - Ensures hosts.sh vars are properly exported to Python
#   - Prevents "Missing environment variables" errors
#   - Standardizes FMC SDK path setup across all scripts
#   - Provides consistent error handling patterns
#
# Key pattern: set -a; source hosts.sh; set +a && python3 << 'EOF'
#   ↓
#   Exports all vars from hosts.sh to this shell
#   ↓
#   && chains to Python execution (preserves exported vars)
#   ↓
#   Child Python process inherits exported environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

cd "${REPO_ROOT}"

# ============================================================================
# PREFLIGHT CHECKS
# ============================================================================

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH"
  exit 1
fi

if [[ ! -f "hosts.sh" ]]; then
  echo "ERROR: hosts.sh not found at repo root"
  echo "Remediation: cp hosts.sh.example hosts.sh && edit with real values"
  exit 1
fi

# Check for FMC SDK installation
if [[ ! -d "scc-fm-sdk/scc_firewall_manager_sdk" ]]; then
  echo "ERROR: FMC SDK not found at scc-fm-sdk/"
  echo "Remediation:"
  echo "  mkdir -p scc-fm-sdk"
  echo "  cd scc-fm-sdk"
  echo "  pip install --target . scc-firewall-manager-sdk"
  exit 1
fi

# ============================================================================
# EXECUTE PYTHON WORKFLOW
# ============================================================================
# 
# CRITICAL: set -a; source hosts.sh; set +a BEFORE python3
#
# Do NOT do this:
#   python3 << 'EOF'
#   os.system("source hosts.sh")  # ❌ Won't work — subshell
#   ...
#
# DO this:
#   set -a; source hosts.sh; set +a && python3 << 'EOF'
#   # vars now available to Python process
#   ...
# ============================================================================

set -a
source "hosts.sh"
set +a

python3 << 'PYTHON_EOF'

import sys
import os
from typing import Optional, List, Dict, Any

# Add FMC SDK to path
sys.path.insert(0, '/home/wolfy/scc/scc-fm-sdk')

# Import FMC SDK components
from scc_firewall_manager_sdk import ApiClient, Configuration
from scc_firewall_manager_sdk.api.inventory_api import InventoryApi
from scc_firewall_manager_sdk.api.object_management_api import ObjectManagementApi
from scc_firewall_manager_sdk.api.device_deployments_api import DeviceDeploymentsApi

# ============================================================================
# ENVIRONMENT VALIDATION
# ============================================================================

def validate_environment() -> tuple[str, str]:
    """Validate required environment variables."""
    api_key = os.getenv('SCC_FMC_API_KEY')
    base_url = os.getenv('SCC_EDGE_URL')
    
    if not api_key:
        print("✗ SCC_FMC_API_KEY not set")
        print("  Load environment: set -a; source hosts.sh; set +a")
        sys.exit(1)
    
    if not base_url:
        print("✗ SCC_EDGE_URL not set")
        print("  Configure hosts.sh with FMC API endpoint")
        sys.exit(1)
    
    print(f"✓ Environment configured")
    print(f"  Endpoint: {base_url}")
    print(f"  Token: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    return api_key, base_url

# ============================================================================
# SDK CLIENT SETUP
# ============================================================================

def setup_client(api_key: str, base_url: str) -> ApiClient:
    """Configure and return FMC API client."""
    config = Configuration(
        host=base_url,
        access_token=api_key
    )
    
    client = ApiClient(configuration=config)
    print("✓ FMC API client configured")
    print()
    
    return client

# ============================================================================
# CUSTOMIZE THIS SECTION FOR YOUR WORKFLOW
# ============================================================================

def main():
    """Main workflow execution."""
    
    print("\n" + "=" * 80)
    print("FMC SDK Workflow")
    print("=" * 80 + "\n")
    
    # Validate environment
    api_key, base_url = validate_environment()
    
    # Setup API client
    client = setup_client(api_key, base_url)
    
    # Create API instances
    inventory_api = InventoryApi(client)
    # object_api = ObjectManagementApi(client)
    # deploy_api = DeviceDeploymentsApi(client)
    
    try:
        # EXAMPLE: List devices
        print("Fetching device inventory...")
        devices_response = inventory_api.get_devices()
        
        print(f"✓ Found {devices_response.count} devices")
        print()
        
        for device in devices_response.items:
            print(f"  Device: {device.name}")
            print(f"    UID: {device.uid}")
            print(f"    Type: {device.device_type}")
            print(f"    State: {device.connectivity_state}")
            print()
        
        # ADD YOUR WORKFLOW LOGIC BELOW THIS LINE
        # 
        # Examples:
        # 
        # 1. Query specific device:
        #    device = inventory_api.get_device(device_uid="...")
        # 
        # 2. Create network object:
        #    network_obj = object_api.create_network_object(...)
        # 
        # 3. Deploy configuration:
        #    deployment = deploy_api.deploy_device_changes(device_uid="...")
        # 
        # 4. List managers (cdFMC):
        #    managers = inventory_api.get_device_managers(
        #        q="deviceType:CDFMC"
        #    )
        # 
        # See FMC API documentation:
        #   - .github/skills/learn_fm_api/SKILL.md
        #   - scripts/README.md (SDK section)
        #   - https://scc-firewall-manager-sdk.readthedocs.io/
        
        print("=" * 80)
        print("✓ Workflow completed successfully")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        print("=" * 80 + "\n")
        sys.exit(1)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    main()

PYTHON_EOF

exit_code=$?
if [[ $exit_code -ne 0 ]]; then
  echo "Workflow failed with exit code $exit_code"
  exit $exit_code
fi

echo "Script completed successfully"
