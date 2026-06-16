---
name: scc_fm
description: Security Cloud Control Firewall Management Center API utilities. Provides FMC API connectivity testing, device discovery, cdFMC resolution, and SDK integration helpers.
---

# Security Cloud Control FMC Utilities Skill

This skill provides utilities for connecting to Cisco Security Cloud Control Firewall Management Center (FMC) API, with authentication testing, device discovery, and Python SDK integration support.

## When to Use This Skill

- Testing FMC API connectivity and authentication
- Discovering devices and cdFMC instances
- Troubleshooting FMC API access issues
- Getting device inventory quickly
- Testing SDK integration
- Debugging authentication or endpoint problems

## What This Skill Provides

### Files in `.github/skills/scc_fm/`

All scripts require only `curl` and `python3` (stdlib) — no venv or pip install needed for basic scripts.

1. **check_fmc_api.sh** - FMC API connectivity test
   - Tests authentication with FMC API token
   - Verifies endpoint accessibility
   - Reports available API resources
   - Prints `RESULT: PASS` / `FAIL` summary
   - Usage: `bash .github/skills/scc_fm/check_fmc_api.sh`

2. **get_devices.sh** - Quick device inventory
   - Calls `GET /v1/inventory/devices` 
   - Returns device count, names, types, and connectivity status
   - Lightweight alternative to full SDK
   - Usage: `bash .github/skills/scc_fm/get_devices.sh`

3. **get_cdfmc.sh** - Discover cdFMC instance
   - Queries for cloud-delivered FMC (cdFMC)
   - Returns cdFMC UID and domain UUID
   - Required for cdFMC-specific API operations
   - Usage: `bash .github/skills/scc_fm/get_cdfmc.sh`

4. **test_sdk.py** - SDK connectivity test (requires SDK installation)
   - Tests Python SDK with local installation
   - Validates SDK configuration and imports
   - Makes sample API call to verify connectivity
   - Usage: `python3 .github/skills/scc_fm/test_sdk.py`

## Quick Start

No installation required for basic utilities. All scripts source `hosts.sh` automatically.

### Configuration

Credentials are sourced automatically from `hosts.sh` at the repo root:

```bash
SCC_FMC_API_KEY   — FMC API token (Bearer token)
SCC_EDGE_URL      — FMC API base URL (e.g., https://api.us.security.cisco.com/firewall)
SCC_ORG_UUID      — Organization UUID
```

> **Regional Endpoints**: FMC API is available in US, EU, APJ, Australia, India, UAE, and FedRAMP regions.
> Ensure `SCC_EDGE_URL` matches your deployment region.

### Test FMC API connectivity

```bash
bash .github/skills/scc_fm/check_fmc_api.sh
```

Expected: Authentication successful, device inventory accessible, `RESULT: PASS`.

### List devices

```bash
bash .github/skills/scc_fm/get_devices.sh
```

Returns device count and basic inventory information.

### Discover cdFMC

```bash
bash .github/skills/scc_fm/get_cdfmc.sh
```

Returns cdFMC UID and domain UUID if present in your tenant.

### Test Python SDK (requires SDK installation)

```bash
python3 .github/skills/scc_fm/test_sdk.py
```

Validates SDK installation at `/home/wolfy/scc/scc-fm-sdk/` and makes test API call.

## Architecture

```
check_fmc_api.sh / get_devices.sh / get_cdfmc.sh
    └── curl → FMC API → Security Cloud Control Firewall Manager

test_sdk.py
    └── scc-firewall-manager-sdk → FMC API → Security Cloud Control
```

All bash scripts:
1. Source `hosts.sh` from the repo root for credentials
2. Make direct `curl` calls with `Bearer` auth to FMC endpoints
3. Parse JSON responses with `python3` stdlib or `jq`

## Key Features

- **No dependencies for basic scripts**: Only `curl` and `python3` stdlib
- **Credential-free setup**: Automatically loads from `hosts.sh`
- **Device discovery**: Quick device inventory without SDK overhead
- **cdFMC resolution**: Discover cdFMC UID for specialized operations
- **SDK validation**: Test Python SDK integration

## Token Lifecycle

FMC API tokens have different expiration policies than SCC platform tokens. When your FMC token expires:

### When Your FMC Token Expires
1. Visit https://security.cisco.com → **Inventory** → Select cdFMC
2. Or visit your regional portal and navigate to API settings
3. Generate a new API key with appropriate permissions
4. Update `hosts.sh`:
   ```bash
   SCC_FMC_API_KEY="<new_token>"
   ```
5. Verify with `bash .github/skills/scc_fm/check_fmc_api.sh`

> **Important**: FMC API keys require specific role permissions. Ensure your user has at least "Edit-only" or "Read-only" privileges.

## Use Cases

| Task | Script | Notes |
|------|--------|-------|
| Test API connectivity | `bash check_fmc_api.sh` | Quick health check |
| Get device count | `bash get_devices.sh` | Lightweight query |
| Find cdFMC UUID | `bash get_cdfmc.sh` | Required for cdFMC APIs |
| Test SDK setup | `python3 test_sdk.py` | Validates SDK installation |
| Detailed inventory | Use SDK (`example_inventory.py`) | Full device details |

## Python SDK Integration

The FMC agent uses the **SCC Firewall Manager SDK** (v1.20.240) installed at `/home/wolfy/scc/scc-fm-sdk/`.

### SDK vs Curl Scripts

**Use bash scripts when:**
- Quick testing or debugging
- Simple read operations
- Minimal dependencies preferred
- Shell scripting workflows

**Use Python SDK when:**
- Complex automation workflows
- Type safety and IDE support needed
- Batch operations across multiple resources
- Building reusable functions or modules

### SDK Example

See `/home/wolfy/scc/scripts/example_inventory.py` for a complete working example using the SDK.

For SDK documentation, see `/home/wolfy/scc/scripts/README.md` (SDK section).

## Integration with VS Code Agent

This skill complements the [scc-fm-api VS Code agent](../../agents/scc-fm-api.agent.md):

| Use Case | VS Code Agent (@FMC) | This Utility |
|----------|---------------------|--------------|
| Interactive device queries | ✅ Best choice | ❌ |
| Quick device list | ❌ | ✅ Best choice |
| API connectivity testing | ❌ | ✅ Best choice |
| cdFMC discovery | ❌ | ✅ Best choice |
| Complex automation | ✅ Use SDK via agent | ✅ Use SDK scripts |

## Troubleshooting

### Error: "401 Unauthorized"
- Check `SCC_FMC_API_KEY` is set correctly in `hosts.sh`
- Verify token hasn't expired
- Ensure API key has required permissions (Read-only minimum)
- Run `bash check_fmc_api.sh` for diagnostic information

### Error: "404 Not Found"
- Verify `SCC_EDGE_URL` matches your region
- Check endpoint path is correct (should start with `/v1/`)
- Ensure you're using FMC API token, not SCC platform token

### No devices returned
- Verify devices are onboarded in your tenant
- Check API key has inventory read permissions
- Use `bash get_devices.sh` to see raw API response

### SDK import errors
- Ensure SDK is installed: `ls /home/wolfy/scc/scc-fm-sdk/scc_firewall_manager_sdk/`
- Verify Python path includes SDK directory
- See `/home/wolfy/scc/scripts/README.md` for SDK setup

## Related Documentation

- [FMC Agent](../../agents/scc-fm-api.agent.md) - Interactive agent for FMC operations
- [learn_fm_api Skill](../learn_fm_api/SKILL.md) - Comprehensive FMC API reference
- [Scripts README](/home/wolfy/scc/scripts/README.md) - SDK documentation and examples
- [example_inventory.py](/home/wolfy/scc/scripts/example_inventory.py) - Working SDK example
