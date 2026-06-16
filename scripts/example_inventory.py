#!/usr/bin/env python3
"""
Example: Using the SCC Firewall Manager SDK

This script demonstrates how to use the locally installed SDK to query
device inventory from Security Cloud Control.

Prerequisites:
    1. Load environment: set -a; source hosts.sh; set +a
    2. Ensure SCC_FMC_API_KEY and SCC_EDGE_URL are set

Usage:
    python3 example_inventory.py
"""

import sys
import os

# Add local SDK to Python path
sys.path.insert(0, '/home/wolfy/scc/scc-fm-sdk')

from scc_firewall_manager_sdk import ApiClient, Configuration
from scc_firewall_manager_sdk.api.inventory_api import InventoryApi

def main():
    # Get credentials from environment
    api_key = os.getenv('SCC_FMC_API_KEY')
    base_url = os.getenv('SCC_EDGE_URL')
    
    if not api_key or not base_url:
        print("❌ Error: SCC_FMC_API_KEY or SCC_EDGE_URL not set")
        print("   Please run: set -a; source hosts.sh; set +a")
        return 1
    
    print("✓ Environment configured")
    print(f"  Endpoint: {base_url}")
    print(f"  Token: {api_key[:10]}...{api_key[-4:]}\n")
    
    # Configure API client
    config = Configuration(
        host=base_url,
        access_token=api_key
    )
    
    # Create API client
    client = ApiClient(configuration=config)
    
    # Create Inventory API instance
    inventory_api = InventoryApi(client)
    
    try:
        print("📋 Fetching device inventory...\n")
        
        # Get all devices
        response = inventory_api.get_devices()
        
        print("=" * 80)
        print(f"Device Inventory Summary")
        print("=" * 80)
        print(f"Total Devices: {response.count}")
        print(f"Showing: {len(response.items)} of {response.count}")
        print("=" * 80 + "\n")
        
        # Display device details
        for device in response.items:
            print(f"Device: {device.name}")
            print(f"  UID: {device.uid}")
            print(f"  Type: {device.device_type}")
            print(f"  Address: {device.address}")
            print(f"  State: {device.connectivity_state}")
            print(f"  Config State: {device.config_state}")
            
            if hasattr(device, 'software_version'):
                print(f"  Software: {device.software_version}")
            
            if hasattr(device, 'serial'):
                print(f"  Serial: {device.serial}")
            
            print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
