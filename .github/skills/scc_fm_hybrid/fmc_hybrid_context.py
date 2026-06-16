#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FMC Hybrid Context — thin wrappers over scc-firewall-manager-sdk APIs.

MCP path  : Discovery / context / read queries (via VS Code MCP tools)
SDK path  : Deterministic writes — delegates directly to FMC SDK API modules

SDK location: /home/wolfy/scc/scc-fm-sdk/ (installed via pip --target)

Usage:
    with FMCHybridContext() as ctx:
        # Read via SDK or MCP tools in the agent:
        devices = ctx.inventory.get_devices()
        cdfmc = ctx.get_cdfmc()

        # Deterministic writes (after operator confirmation):
        # ctx.create_network_object("web-servers", "192.168.1.0/24")
        # ctx.deploy_device_changes(device_uid)
"""

import os
import sys
from enum import Enum
from typing import Dict, Any, Optional, List

# ---------------------------------------------------------------------------
# Inject FMC SDK into path
# Layout: FMC SDK installed at /home/wolfy/scc/scc-fm-sdk/
# ---------------------------------------------------------------------------
_FMC_SDK_PATH = "/home/wolfy/scc/scc-fm-sdk"
if _FMC_SDK_PATH not in sys.path:
    sys.path.insert(0, _FMC_SDK_PATH)

from scc_firewall_manager_sdk import ApiClient, Configuration  # noqa: E402
from scc_firewall_manager_sdk.api.inventory_api import InventoryApi  # noqa: E402

# Optional APIs — import only if available
try:
    from scc_firewall_manager_sdk.api.object_management_api import ObjectManagementApi  # noqa: E402
except ImportError:
    ObjectManagementApi = None

try:
    from scc_firewall_manager_sdk.api.device_deployments_api import DeviceDeploymentsApi  # noqa: E402
except ImportError:
    DeviceDeploymentsApi = None

try:
    from scc_firewall_manager_sdk.api.remote_access_monitoring_api import RemoteAccessMonitoringApi  # noqa: E402
except ImportError:
    RemoteAccessMonitoringApi = None

try:
    from scc_firewall_manager_sdk.api.transactions_api import TransactionsApi  # noqa: E402
except ImportError:
    TransactionsApi = None


# ---------------------------------------------------------------------------
# Intent routing
# ---------------------------------------------------------------------------

class OperationIntent(Enum):
    DISCOVER = "mcp"   # Read / exploration → MCP tools
    WRITE    = "sdk"   # Deterministic mutation → SDK wrappers


_WRITE_KEYWORDS = {
    "create", "add", "deploy", "update", "delete", "remove", "patch",
    "onboard", "configure", "enable", "disable", "modify", "edit",
}
_DISCOVER_KEYWORDS = {
    "list", "show", "find", "search", "get", "query", "check", "report",
}


# ---------------------------------------------------------------------------
# Hybrid context
# ---------------------------------------------------------------------------

class FMCHybridContext:
    """
    Hybrid context manager — MCP for discovery, SDK for deterministic writes.

    Startup gates (enforced in __enter__):
      1. Credentials    — SCC_FMC_API_KEY, SCC_EDGE_URL present
      2. SDK Install    — /home/wolfy/scc/scc-fm-sdk/ exists
      3. API Access     — Test call to /v1/inventory/devices succeeds
      4. cdFMC Discovery — Cache cdFMC UID if present (warning only)

    Session cache:  cdFMC UID · device name→UID · domain UUID

    Error recovery order:
      1. Verify operation state via read API
      2. Compensate if partial success detected
      3. Operator-facing guidance with retry flag
    """

    def __init__(self):
        self.api_key = os.environ.get("SCC_FMC_API_KEY", "")
        self.base_url = os.environ.get("SCC_EDGE_URL", "")
        
        self._client: Optional[ApiClient] = None
        self._inventory: Optional[InventoryApi] = None
        self._objects: Optional[ObjectManagementApi] = None
        self._deployments: Optional[DeviceDeploymentsApi] = None
        self._ravpn: Optional[RemoteAccessMonitoringApi] = None
        self._transactions: Optional[TransactionsApi] = None
        
        # Session cache
        self._cdfmc_uid: Optional[str] = None
        self._cdfmc_domain_uuid: Optional[str] = None
        self._device_cache: Dict[str, str] = {}  # name → UID

    def __enter__(self):
        """Startup gates + SDK client initialization."""
        self._validate_credentials()
        self._validate_sdk_installation()
        self._initialize_client()
        self._validate_api_access()
        self._discover_cdfmc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup and close SDK client."""
        if self._client:
            # SDK ApiClient doesn't have close() method, just clear reference
            self._client = None
        self.clear_cache()
        return False

    # -----------------------------------------------------------------------
    # Startup Gates
    # -----------------------------------------------------------------------

    def _validate_credentials(self):
        """Gate 1: Verify required environment variables."""
        if not self.api_key:
            raise EnvironmentError(
                "Missing SCC_FMC_API_KEY environment variable. "
                "Load credentials: set -a; source hosts.sh; set +a"
            )
        if not self.base_url:
            raise EnvironmentError(
                "Missing SCC_EDGE_URL environment variable. "
                "Load credentials: set -a; source hosts.sh; set +a"
            )
        
        # Validate URL format
        if not self.base_url.startswith("https://"):
            raise ValueError(f"SCC_EDGE_URL must start with https://: {self.base_url}")

    def _validate_sdk_installation(self):
        """Gate 2: Verify FMC SDK is installed."""
        if not os.path.exists(_FMC_SDK_PATH):
            raise EnvironmentError(
                f"FMC SDK not found at {_FMC_SDK_PATH}. "
                "Install: pip install --target /home/wolfy/scc/scc-fm-sdk scc-firewall-manager-sdk"
            )
        
        sdk_module = os.path.join(_FMC_SDK_PATH, "scc_firewall_manager_sdk")
        if not os.path.exists(sdk_module):
            raise EnvironmentError(
                f"SDK module not found at {sdk_module}. "
                "Verify installation or reinstall SDK."
            )

    def _initialize_client(self):
        """Initialize SDK API client with configuration."""
        config = Configuration(
            host=self.base_url,
            access_token=self.api_key
        )
        
        # Set additional configuration
        config.verify_ssl = True
        
        self._client = ApiClient(configuration=config)
        
        # Initialize API modules
        self._inventory = InventoryApi(self._client)
        
        if ObjectManagementApi:
            self._objects = ObjectManagementApi(self._client)
        
        if DeviceDeploymentsApi:
            self._deployments = DeviceDeploymentsApi(self._client)
        
        if RemoteAccessMonitoringApi:
            self._ravpn = RemoteAccessMonitoringApi(self._client)
        
        if TransactionsApi:
            self._transactions = TransactionsApi(self._client)

    def _validate_api_access(self):
        """Gate 3: Test API connectivity with a safe read call."""
        try:
            # Test with minimal device query
            response = self._inventory.get_devices(limit="1")
            print(f"✓ FMC API access validated (found {response.count} devices)")
        except Exception as e:
            raise ConnectionError(
                f"FMC API access test failed: {e}\n"
                "Check credentials and SCC_EDGE_URL"
            )

    def _discover_cdfmc(self):
        """Gate 4: Discover and cache cdFMC UID (warning only if not found)."""
        try:
            managers = self._inventory.get_device_managers()
            if managers and managers.items:
                # Find first cdFMC
                for manager in managers.items:
                    if manager.device_type in ("cdFMC", "FMC"):
                        self._cdfmc_uid = manager.uid
                        if hasattr(manager, 'domain_uuid'):
                            self._cdfmc_domain_uuid = manager.domain_uuid
                        print(f"✓ cdFMC discovered: {manager.name} ({self._cdfmc_uid})")
                        return
                
                print("⚠ No cdFMC found in device managers")
            else:
                print("⚠ No device managers found")
        except Exception as e:
            print(f"⚠ cdFMC discovery failed: {e} (non-blocking)")

    # -----------------------------------------------------------------------
    # SDK API Access (Properties)
    # -----------------------------------------------------------------------

    @property
    def inventory(self) -> InventoryApi:
        """Direct access to InventoryApi."""
        if not self._inventory:
            raise RuntimeError("Context not initialized. Use 'with FMCHybridContext()' pattern.")
        return self._inventory

    @property
    def objects(self) -> ObjectManagementApi:
        """Direct access to ObjectManagementApi."""
        if not self._objects:
            raise RuntimeError(
                "ObjectManagementApi not available. "
                "Verify SDK installation includes this module."
            )
        return self._objects

    @property
    def deployments(self) -> DeviceDeploymentsApi:
        """Direct access to DeviceDeploymentsApi."""
        if not self._deployments:
            raise RuntimeError(
                "DeviceDeploymentsApi not available. "
                "Verify SDK installation includes this module."
            )
        return self._deployments

    @property
    def ravpn(self) -> RemoteAccessMonitoringApi:
        """Direct access to RemoteAccessMonitoringApi."""
        if not self._ravpn:
            raise RuntimeError(
                "RemoteAccessMonitoringApi not available. "
                "Verify SDK installation includes this module."
            )
        return self._ravpn

    @property
    def transactions(self) -> TransactionsApi:
        """Direct access to TransactionsApi."""
        if not self._transactions:
            raise RuntimeError(
                "TransactionsApi not available. "
                "Verify SDK installation includes this module."
            )
        return self._transactions

    # -----------------------------------------------------------------------
    # Convenience Methods
    # -----------------------------------------------------------------------

    def get_cdfmc(self) -> Optional[Dict[str, Any]]:
        """Get cached cdFMC information."""
        if self._cdfmc_uid:
            return {
                "uid": self._cdfmc_uid,
                "domain_uuid": self._cdfmc_domain_uuid,
            }
        return None

    def get_device_by_name(self, name: str):
        """Find device by name, with caching."""
        # Check cache first
        if name in self._device_cache:
            device_uid = self._device_cache[name]
            try:
                return self.inventory.get_device(device_uid)
            except Exception:
                # Cache miss, re-fetch
                del self._device_cache[name]
        
        # Search all devices
        devices = self.inventory.get_devices()
        for device in devices.items:
            if device.name == name:
                self._device_cache[name] = device.uid
                return device
        
        return None

    def get_devices_by_type(self, device_type: str) -> List[Any]:
        """Filter devices by type (ASA, FTD, IOS, etc.)."""
        devices = self.inventory.get_devices()
        return [d for d in devices.items if d.device_type == device_type]

    def wait_for_transaction(self, transaction_uid: str, timeout: int = 300) -> Any:
        """Poll transaction until complete or timeout."""
        import time
        
        if not self._transactions:
            raise RuntimeError("TransactionsApi not available")
        
        start = time.time()
        while time.time() - start < timeout:
            status = self._transactions.get_transaction(transaction_uid)
            
            if hasattr(status, 'state'):
                if status.state in ('COMPLETED', 'SUCCESS', 'DONE'):
                    return status
                elif status.state in ('FAILED', 'ERROR'):
                    raise RuntimeError(f"Transaction failed: {status.state}")
            
            time.sleep(5)
        
        raise TimeoutError(f"Transaction {transaction_uid} timed out after {timeout}s")

    # -----------------------------------------------------------------------
    # Intent Routing
    # -----------------------------------------------------------------------

    def classify_intent(self, operation_description: str) -> OperationIntent:
        """
        Classify operation intent based on description.
        
        Returns:
            OperationIntent.WRITE for mutations
            OperationIntent.DISCOVER for read/query operations
        """
        desc_lower = operation_description.lower()
        
        # Check for write keywords
        if any(keyword in desc_lower for keyword in _WRITE_KEYWORDS):
            return OperationIntent.WRITE
        
        # Check for discover keywords
        if any(keyword in desc_lower for keyword in _DISCOVER_KEYWORDS):
            return OperationIntent.DISCOVER
        
        # Default to DISCOVER for safety
        return OperationIntent.DISCOVER

    def route_operation(self, intent: OperationIntent) -> str:
        """
        Route operation to appropriate execution path.
        
        Returns:
            "sdk" for deterministic writes
            "mcp" for discovery operations
        """
        return intent.value

    # -----------------------------------------------------------------------
    # Session Cache Management
    # -----------------------------------------------------------------------

    def clear_cache(self):
        """Clear session cache."""
        self._device_cache.clear()
        self._cdfmc_uid = None
        self._cdfmc_domain_uuid = None

    # -----------------------------------------------------------------------
    # Thin Write Wrappers (Placeholders)
    # -----------------------------------------------------------------------
    # These methods provide a clean interface for common write operations
    # They should only be called after operator confirmation

    def create_network_object(self, name: str, value: str, description: str = ""):
        """
        Create network object.
        
        NOTE: Requires ObjectManagementApi. Placeholder implementation.
        """
        if not self._objects:
            raise RuntimeError("ObjectManagementApi not available")
        
        raise NotImplementedError(
            "create_network_object requires full ObjectManagementApi integration. "
            "Use ctx.objects API directly or implement based on API spec."
        )

    def deploy_device_changes(self, device_uid: str):
        """
        Deploy pending changes to device.
        
        NOTE: Requires DeviceDeploymentsApi. Placeholder implementation.
        """
        if not self._deployments:
            raise RuntimeError("DeviceDeploymentsApi not available")
        
        raise NotImplementedError(
            "deploy_device_changes requires full DeviceDeploymentsApi integration. "
            "Use ctx.deployments API directly or implement based on API spec."
        )


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def smoke_test():
    """Safe smoke test — reads device inventory only."""
    try:
        with FMCHybridContext() as ctx:
            print("\n=== FMC Hybrid Context Smoke Test ===\n")
            
            # Test device inventory
            devices = ctx.inventory.get_devices()
            print(f"Total devices: {devices.count}")
            
            if devices.items:
                print("\nDevices:")
                for device in devices.items:
                    print(f"  - {device.name:<25} {device.device_type:<10} {device.connectivity_state}")
            
            # Test cdFMC discovery
            cdfmc = ctx.get_cdfmc()
            if cdfmc:
                print(f"\ncdFMC: {cdfmc['uid']}")
            
            # Test intent routing
            print("\nIntent Classification:")
            tests = [
                "create network object",
                "show device inventory",
                "deploy changes to device",
                "list access rules",
            ]
            for test in tests:
                intent = ctx.classify_intent(test)
                route = ctx.route_operation(intent)
                print(f"  '{test}' → {intent.name} (route: {route})")
            
            print("\n✓ Smoke test passed\n")
            
    except Exception as e:
        print(f"\n✗ Smoke test failed: {e}\n")
        raise


if __name__ == "__main__":
    smoke_test()
