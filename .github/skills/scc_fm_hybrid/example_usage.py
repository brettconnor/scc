#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Using FMC Hybrid Context

Demonstrates key features:
- Device discovery and filtering
- Intent classification
- Session caching
- Convenience methods
"""

import sys
sys.path.insert(0, ".github/skills/scc_fm_hybrid")

from fmc_hybrid_context import FMCHybridContext, OperationIntent

def main():
    print("=== FMC Hybrid Context Usage Examples ===\n")
    
    with FMCHybridContext() as ctx:
        # Example 1: List all devices
        print("1. List all devices:")
        devices = ctx.inventory.get_devices()
        print(f"   Total: {devices.count} devices")
        for device in devices.items:
            print(f"   - {device.name:<25} {device.device_type:<15} {device.connectivity_state}")
        
        # Example 2: Get device by name (with caching)
        print("\n2. Find device by name (cached):")
        device = ctx.get_device_by_name("asav-0")
        if device:
            print(f"   Name: {device.name}")
            print(f"   UID: {device.uid}")
            print(f"   Type: {device.device_type}")
            print(f"   Address: {device.address}")
            print(f"   Version: {device.software_version}")
        
        # Example 3: Filter devices by type
        print("\n3. Filter devices by type:")
        asa_devices = ctx.get_devices_by_type("ASA")
        print(f"   ASA devices: {len(asa_devices)}")
        for dev in asa_devices:
            print(f"   - {dev.name} ({dev.address})")
        
        ios_devices = ctx.get_devices_by_type("IOS")
        print(f"   IOS devices: {len(ios_devices)}")
        for dev in ios_devices:
            print(f"   - {dev.name} ({dev.address})")
        
        # Example 4: Get cdFMC info
        print("\n4. Get cdFMC information:")
        cdfmc = ctx.get_cdfmc()
        if cdfmc:
            print(f"   cdFMC UID: {cdfmc['uid']}")
            if cdfmc.get('domain_uuid'):
                print(f"   Domain UUID: {cdfmc['domain_uuid']}")
        else:
            print("   No cdFMC found")
        
        # Example 5: Intent classification
        print("\n5. Intent classification:")
        test_operations = [
            "create network object for web servers",
            "show device inventory",
            "deploy configuration to device",
            "list access control rules",
            "add new ASA device",
            "get RA VPN sessions",
        ]
        
        for op in test_operations:
            intent = ctx.classify_intent(op)
            route = ctx.route_operation(intent)
            symbol = "✎" if intent == OperationIntent.WRITE else "👁"
            print(f"   {symbol} '{op}'")
            print(f"      → {intent.name} (route: {route})")
        
        # Example 6: Device managers
        print("\n6. Device managers:")
        managers = ctx.inventory.get_device_managers()
        if managers and managers.items:
            print(f"   Total: {managers.count} managers")
            for mgr in managers.items:
                print(f"   - {mgr.name:<25} {mgr.device_type}")
        else:
            print("   No device managers found")

if __name__ == "__main__":
    main()
