#!/usr/bin/env python3
"""
test_sdk.py - Test SCC Firewall Manager SDK installation and connectivity

Usage:
    python3 .github/skills/scc_fm/test_sdk.py

Validates:
- SDK is installed at /home/wolfy/scc/scc-fm-sdk/
- SDK imports work correctly
- API client can be configured
- Test API call succeeds
"""

import sys
import os

# Add SDK to path
SDK_PATH = '/home/wolfy/scc/scc-fm-sdk'
sys.path.insert(0, SDK_PATH)

def check_sdk_installation():
    """Verify SDK is installed"""
    print("=" * 60)
    print("SCC Firewall Manager SDK Test")
    print("=" * 60)
    print()
    
    print(f"Checking SDK installation at: {SDK_PATH}")
    
    if not os.path.exists(SDK_PATH):
        print(f"✗ SDK directory not found: {SDK_PATH}")
        print()
        print("Install SDK with:")
        print(f"  mkdir -p {SDK_PATH}")
        print(f"  cd {SDK_PATH}")
        print("  pip install --target . scc-firewall-manager-sdk")
        return False
    
    print("✓ SDK directory exists")
    
    # Check for main SDK package
    sdk_package = os.path.join(SDK_PATH, 'scc_firewall_manager_sdk')
    if not os.path.exists(sdk_package):
        print(f"✗ SDK package not found: {sdk_package}")
        return False
    
    print("✓ SDK package found")
    print()
    
    return True

def test_sdk_imports():
    """Test SDK imports"""
    print("Testing SDK imports...")
    
    try:
        from scc_firewall_manager_sdk import ApiClient, Configuration
        print("✓ Core SDK modules imported")
    except ImportError as e:
        print(f"✗ Failed to import core SDK: {e}")
        return False
    
    try:
        from scc_firewall_manager_sdk.api.inventory_api import InventoryApi
        print("✓ InventoryApi imported")
    except ImportError as e:
        print(f"✗ Failed to import InventoryApi: {e}")
        return False
    
    print()
    return True

def test_api_connectivity():
    """Test API connectivity with SDK"""
    print("Testing API connectivity...")
    
    # Get credentials from environment
    api_key = os.getenv('SCC_FMC_API_KEY')
    base_url = os.getenv('SCC_EDGE_URL')
    
    if not api_key:
        print("✗ SCC_FMC_API_KEY not set")
        print("  Load environment: set -a; source hosts.sh; set +a")
        return False
    
    if not base_url:
        print("✗ SCC_EDGE_URL not set")
        print("  Load environment: set -a; source hosts.sh; set +a")
        return False
    
    print(f"✓ Credentials loaded")
    print(f"  Endpoint: {base_url}")
    print(f"  Token: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    try:
        from scc_firewall_manager_sdk import ApiClient, Configuration
        from scc_firewall_manager_sdk.api.inventory_api import InventoryApi
        
        # Configure API client
        config = Configuration(
            host=base_url,
            access_token=api_key
        )
        
        print("✓ SDK configuration created")
        
        # Create client
        client = ApiClient(configuration=config)
        print("✓ API client created")
        
        # Create inventory API
        inventory_api = InventoryApi(client)
        print("✓ InventoryApi initialized")
        print()
        
        # Make test API call
        print("Making test API call (get_devices with limit=1)...")
        response = inventory_api.get_devices(limit="1")
        
        print("✓ API call succeeded")
        print(f"  Total devices: {response.count}")
        
        if response.items:
            device = response.items[0]
            print(f"  Sample device: {device.name} ({device.device_type})")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ API call failed: {e}")
        return False

def main():
    """Main test flow"""
    
    # Test 1: SDK installation
    if not check_sdk_installation():
        sys.exit(1)
    
    # Test 2: SDK imports
    if not test_sdk_imports():
        sys.exit(1)
    
    # Test 3: API connectivity
    if not test_api_connectivity():
        sys.exit(1)
    
    # All tests passed
    print("=" * 60)
    print("✓ All tests passed")
    print("=" * 60)
    print()
    print("SDK is properly installed and configured.")
    print()
    print("Next steps:")
    print("  - Run example: python3 scripts/example_inventory.py")
    print("  - See SDK docs: cat scripts/README.md")
    print("  - Use @FMC agent for interactive operations")

if __name__ == '__main__':
    main()
