---
description: "Hybrid MCP discovery + deterministic SDK write wrapper for FMC workflows"
hints:
  - "Use when executing FMC write operations (device onboarding, object creation, policy deployment) that require both discovery context and mutation"
  - "Provides pre-configured SDK client with automatic credential loading — no need to pass tokens explicitly"
  - "Intent routing automatically classifies operations as WRITE (sdk) or DISCOVER (mcp) to coordinate MCP + SDK execution"
  - "Session cache prevents redundant API calls for device/object lookups within one workflow cycle"
  - "Error recovery enforces API verify → compensate → operator guidance precedence"
  - "Startup gates verify credentials, SDK installation, API access, and cdFMC discovery before any operation"
---

# FMC Hybrid Skill

Provides a thin Python wrapper over the `scc-firewall-manager-sdk`, combining MCP discovery with deterministic SDK writes in one context manager for use by the FMC agent.

## When to Use This Skill

- When the FMC agent needs to execute write operations (device onboarding, object creation, policy deployment)
- When wiring MCP discovery results into SDK execution calls
- When building firewall workflows that mix context (MCP) with mutation (SDK)
- When debugging or testing FMC write operations independently of the agent

## Files

| File | Purpose |
|------|---------|
| `fmc_hybrid_context.py` | Thin wrapper context manager — uses `scc-firewall-manager-sdk` APIs |
| `bootstrap.sh` | One-command preflight: SDK check, hosts.sh export, and smoke test |

## Architecture

```
FMC Agent
    │
    ├── MCP tools (security-cloud-control/*)   ← Discovery / context / NLP reads
    │
    └── fmc_hybrid_context.py                  ← Deterministic writes
            │
            └── scc-firewall-manager-sdk/      ← FMC SDK installation
                    ├── InventoryApi
                    ├── ObjectManagementApi
                    ├── DeviceDeploymentsApi
                    └── [30+ API modules]
```

## Quick Start

### One-command bootstrap (recommended)

```bash
bash .github/skills/scc_fm_hybrid/bootstrap.sh
```

This command:
- verifies FMC SDK is installed at `/home/wolfy/scc/scc-fm-sdk`
- exports variables from `hosts.sh` for child processes
- runs the safe hybrid smoke test (queries device inventory)

### 0) Verify SDK Installation

The hybrid context requires the FMC SDK installed at `/home/wolfy/scc/scc-fm-sdk/`.

Check installation:
```bash
ls /home/wolfy/scc/scc-fm-sdk/scc_firewall_manager_sdk/
```

If not installed, see:
```bash
# Installation documented in scripts/README.md
mkdir -p /home/wolfy/scc/scc-fm-sdk
cd /home/wolfy/scc/scc-fm-sdk
pip install --target . scc-firewall-manager-sdk
```

### 1) Export credentials to Python process (CRITICAL)

**⚠️ IMPORTANT**: Environment variables must be sourced BEFORE invoking Python. The hybrid context reads credentials from the parent shell environment.

#### Standard Pattern (Recommended)

```bash
set -a; source hosts.sh; set +a && python3 << 'EOF'
# Your Python code here
EOF
```

This pattern:
- ✓ Exports `hosts.sh` vars to the shell
- ✓ Chains to Python execution with `&&`
- ✓ Passes vars to child Python process
- ✓ Works in one-liners and shell scripts
- ✓ **Prevents `Missing environment variables` errors**

#### Example: List devices

```bash
set -a; source hosts.sh; set +a && python3 << 'EOF'
import sys
sys.path.insert(0, ".github/skills/scc_fm_hybrid")
from fmc_hybrid_context import FMCHybridContext

with FMCHybridContext() as ctx:
    devices = ctx.inventory.get_devices()
    
    print(f"Total devices: {devices.count}")
    for device in devices.items:
        print(f"  {device.name:<25} {device.device_type:<10} {device.connectivity_state}")
EOF
```

### 2) Use the context manager

```python
import sys
sys.path.insert(0, ".github/skills/scc_fm_hybrid")
from fmc_hybrid_context import FMCHybridContext, OperationIntent

with FMCHybridContext() as ctx:
    # Read path — query devices and objects:
    devices = ctx.inventory.get_devices()
    managers = ctx.inventory.get_device_managers()
    
    # Find cdFMC if present:
    cdfmc = ctx.get_cdfmc()  # Returns None if not found
    
    # Object management:
    # networks = ctx.objects.get_network_objects()
    
    # Classify and route intent:
    intent = ctx.classify_intent("onboard new ASA device")
    # → OperationIntent.WRITE  →  route: "sdk"
    
    # Write operations (after operator confirmation):
    # ctx.create_network_object("web-servers", "192.168.1.0/24")
    # ctx.deploy_device_changes(device_uid)
```

### Reusable Workflow Scripts

Reusable workflow templates are owned by the `scc_fm_codegen` skill.

- Canonical template: `.github/skills/scc_fm_codegen/script_template.sh`
- Use `scc_fm_hybrid` for runtime context and deterministic wrappers
- Use `scc_fm_codegen` when generating or maintaining reusable workflow scripts

## Startup Gates

The context manager enforces 4 gates on `__enter__`:

| # | Gate | Check | Blocks on failure |
|---|------|-------|-------------------|
| 1 | Credentials | `SCC_FMC_API_KEY`, `SCC_EDGE_URL` env vars | All operations |
| 2 | SDK Installation | `/home/wolfy/scc/scc-fm-sdk/` exists | All operations |
| 3 | API Access | Test call to `/v1/inventory/devices` | All operations |
| 4 | cdFMC Discovery | Cache cdFMC UID if present | Warning only |

## SDK API Access

Direct access to all FMC SDK API modules via properties:

```python
# Inventory Management
devices = ctx.inventory.get_devices()
device = ctx.inventory.get_device(device_uid)
managers = ctx.inventory.get_device_managers()
device_count = ctx.inventory.get_devices(limit="1")

# Object Management (when ObjectManagementApi is available)
# networks = ctx.objects.get_network_objects()
# services = ctx.objects.get_service_objects()

# Device Deployments
# deployment = ctx.deployments.deploy_device_changes(device_uid)

# Remote Access Monitoring
# sessions = ctx.ravpn.get_ra_vpn_sessions()

# Transactions (for async operations)
# status = ctx.transactions.get_transaction(transaction_uid)
```

## Convenience Methods

Pre-configured helpers that handle common patterns:

| Method | Purpose |
|--------|---------|
| `get_cdfmc()` | Find and cache cdFMC UID (returns None if not found) |
| `get_device_by_name(name)` | Find device by name, returns device object |
| `get_devices_by_type(device_type)` | Filter devices by type (ASA, FTD, IOS, etc.) |
| `wait_for_transaction(uid, timeout)` | Poll transaction until complete or timeout |

## Intent Routing

```python
intent = ctx.classify_intent("create network object for web servers")
# → OperationIntent.WRITE  (route: "sdk")

intent = ctx.classify_intent("show device inventory")
# → OperationIntent.DISCOVER  (route: "mcp")

route = ctx.route_operation(intent)
# → "sdk" or "mcp"
```

## Session Cache

The context maintains a session cache for:
- cdFMC UID and domain UUID
- Device name → UID mappings
- Common object lookups

Cache is cleared on context exit or explicit `ctx.clear_cache()`.

## Error Handling

```python
try:
    with FMCHybridContext() as ctx:
        devices = ctx.inventory.get_devices()
except EnvironmentError as e:
    # Missing credentials
    print(f"Configuration error: {e}")
except ConnectionError as e:
    # API connectivity issues
    print(f"Connection error: {e}")
except Exception as e:
    # Other errors
    print(f"Operation failed: {e}")
```

## Integration with FMC Agent

The FMC agent uses this skill to:
1. Initialize SDK client with proper credentials
2. Combine MCP discovery with SDK writes in workflows
3. Enforce startup gates before write operations
4. Cache discovered resources (cdFMC, devices)
5. Route operations based on intent classification

## FMC-Specific Patterns

### Pattern 1: Device Discovery + Action
```python
with FMCHybridContext() as ctx:
    # Discover devices
    devices = ctx.get_devices_by_type("ASA")
    
    # Perform action on each
    for device in devices:
        # Check health, deploy config, etc.
        pass
```

### Pattern 2: Object Creation with Verification
```python
with FMCHybridContext() as ctx:
    # Create object
    # obj = ctx.objects.create_network_object(...)
    
    # Verify creation
    # objects = ctx.objects.get_network_objects()
    # assert any(o.name == "web-servers" for o in objects.items)
    pass
```

### Pattern 3: Async Operation Tracking
```python
with FMCHybridContext() as ctx:
    # Trigger async operation
    # result = ctx.deployments.deploy_device_changes(device_uid)
    # transaction_uid = result.uid
    
    # Wait for completion
    # status = ctx.wait_for_transaction(transaction_uid, timeout=300)
    pass
```

## Comparison with Direct SDK Usage

### Without Hybrid Context (Manual Setup)
```python
import sys, os
sys.path.insert(0, '/home/wolfy/scc/scc-fm-sdk')
from scc_firewall_manager_sdk import ApiClient, Configuration
from scc_firewall_manager_sdk.api.inventory_api import InventoryApi

api_key = os.getenv('SCC_FMC_API_KEY')
base_url = os.getenv('SCC_EDGE_URL')

config = Configuration(host=base_url, access_token=api_key)
client = ApiClient(configuration=config)
inventory_api = InventoryApi(client)

devices = inventory_api.get_devices()
```

### With Hybrid Context (Automatic Setup)
```python
import sys
sys.path.insert(0, ".github/skills/scc_fm_hybrid")
from fmc_hybrid_context import FMCHybridContext

with FMCHybridContext() as ctx:
    devices = ctx.inventory.get_devices()
```

Benefits:
- ✓ Automatic credential loading
- ✓ Startup validation gates
- ✓ Session caching
- ✓ Consistent error handling
- ✓ Intent routing support

## Troubleshooting

### Error: "Missing environment variables"
```bash
# Solution: Load environment before Python
set -a; source hosts.sh; set +a && python3 your_script.py
```

### Error: "SDK not found"
```bash
# Solution: Install FMC SDK
mkdir -p /home/wolfy/scc/scc-fm-sdk
cd /home/wolfy/scc/scc-fm-sdk
pip install --target . scc-firewall-manager-sdk
```

### Error: "401 Unauthorized"
```bash
# Solution: Regenerate API token
# Update SCC_FMC_API_KEY in hosts.sh
```

### Error: "404 Not Found"
```bash
# Solution: Check SCC_EDGE_URL matches your region
# Verify endpoint: https://api.{region}.security.cisco.com/firewall
```

## Related Skills

- `learn_fm_api` - FMC API reference documentation
- `scc-fm` - Connectivity testing utilities
- `scc_fm_codegen` - Workflow script generation and planning
- `scc_hybrid` - Similar pattern for SCC platform operations

## See Also

- [FMC Agent Documentation](../../agents/scc-fm-api.agent.md)
- [SDK Examples](../../../scripts/example_inventory.py)
- [API Quick Start](../learn_fm_api/getting_started.md)
