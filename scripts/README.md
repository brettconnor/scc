# SCC Scripts

This directory contains utility scripts for Cisco Security Cloud Control operations.

## Credential Context

Scripts in this directory use different API credentials depending on their purpose:

- **SCC Admin scripts**: Use `SCC_API_KEY` and `SCC_URL` for user/group/role management
- **FMC scripts**: Use `SCC_FMC_API_KEY` and `SCC_EDGE_URL` for firewall operations
- Check each script's documentation to confirm which credentials it requires

## Available Scripts

### example_inventory.py

**Type**: FMC Script  
**Credentials**: `SCC_FMC_API_KEY`, `SCC_EDGE_URL`

Demonstrates using the local FMC SDK to query device inventory.

**Usage**:
```bash
set -a; source hosts.sh; set +a
python3 scripts/example_inventory.py
```

### scc_ai_assistant.py

⚠️ **WORK IN PROGRESS** - The AI Assistant API endpoint is not currently available in production. This script is ready for use once the endpoint becomes available.

**Type**: Experimental (API not yet available)  
**Credentials**: To be determined when API becomes available

Python client for interacting with the Cisco Security Cloud Control AI Assistant API.

#### Status

The script is fully implemented but the `/v1/ai-assistant/conversations` endpoint returns 400 errors, indicating the API feature is not yet deployed. Authentication works correctly (verified with FMC inventory API).

**Current Workarounds:**
- Use the FMC agent: `@FMC how many devices are managed?`
- Use direct API calls: `curl "${SCC_EDGE_URL}/v1/inventory/devices"`

#### Features

- ✅ Send questions to the SCC AI Assistant
- ✅ Automatic polling and retry logic
- ✅ Environment variable integration with hosts.sh
- ✅ Interactive and command-line modes
- ✅ Comprehensive error handling
- ✅ Progress indicators and status updates

#### Prerequisites

1. **Python 3.6+** with requests library:
   ```bash
   pip install requests
   ```

2. **Configured hosts.sh** with required environment variables:
   - `SCC_API_KEY` - Your SCC platform API token (JWT)
   - `SCC_REGIONAL_URL` - Regional SCC API endpoint

3. **Load environment variables**:
   ```bash
   set -a; source hosts.sh; set +a
   ```

#### Usage

**Command-line mode** (single question):
```bash
python scripts/scc_ai_assistant.py "How to create VLAN on remote FTD?"
```

**Interactive mode** (continuous conversation):
```bash
python scripts/scc_ai_assistant.py
```

Then type your questions at the prompt. Type `quit` to exit.

#### Example Session

```bash
# Load credentials
$ set -a; source hosts.sh; set +a

# Ask a question
$ python scripts/scc_ai_assistant.py "How do I configure NAT on ASA?"

✓ Environment configured
  Endpoint: https://edge.us.cdo.cisco.com
  Token: eyJhbGciOi...abcd

================================================================================
📝 Question: How do I configure NAT on ASA?
================================================================================

✓ Request sent successfully
  Conversation ID: 1ba692de-8166-4cee-90b5-6f817c3c2008
⏳ Waiting for AI Assistant response...
⏳ Processing... (attempt 5/60)

================================================================================
💬 AI Assistant Response:
================================================================================
To configure NAT on ASA, follow these steps:

1. Access the ASA device through Security Cloud Control
2. Navigate to Devices > Device Management
3. Select your ASA device
...

================================================================================
```

#### Environment Variables Reference

The script uses the following environment variables from `hosts.sh`:

| Variable | Description | Example |
|----------|-------------|---------|
| `SCC_API_KEY` | SCC platform API token (JWT) | `eyJhbGci...` |
| `SCC_REGIONAL_URL` | Regional SCC API endpoint | `https://api.us.security.cisco.com/v1/` |

#### Configuration

You can modify these constants in the script:

- `MAX_RETRIES` - Maximum polling attempts (default: 60)
- `RETRY_DELAY` - Delay between retries in seconds (default: 2)
- `API_TIMEOUT` - HTTP request timeout (default: 30)

#### Error Handling

The script handles common errors:

- **Missing credentials** - Prompts to load hosts.sh
- **HTTP errors** - Displays status code and error message
- **Timeout** - Gracefully exits after max retries
- **Connection errors** - Retries with exponential backoff
- **Invalid responses** - Catches JSON parsing errors

#### API Response Format

The AI Assistant API uses an asynchronous pattern:

1. **POST** `/v1/ai-assistant/conversations` - Create conversation
   - Returns: `{"uid": "conversation-id", ...}`

2. **GET** `/v1/ai-assistant/conversations/{uid}/messages` - Poll for response
   - Returns: `{"status": "completed|pending|failed", "content": "response text"}`

#### Troubleshooting

**Error: SCC_API_KEY not set**
```bash
# Solution: Load environment
set -a; source hosts.sh; set +a
```

**Error: 401 Unauthorized**
```bash
# Solution: Generate a new API token in SCC UI
# Update hosts.sh with SCC_API_KEY
```

**Error: Timeout**
```bash
# Solution: Increase MAX_RETRIES in the script
# Or check if the AI Assistant service is available
```

**Error: Module not found**
```bash
# Solution: Install dependencies
pip install requests
```

#### Security Best Practices

- ✅ Never commit `hosts.sh` with real credentials
- ✅ Use environment variables (not hardcoded tokens)
- ✅ Rotate API tokens regularly
- ✅ Use regional endpoints closest to your location
- ✅ Monitor API usage and rate limits

#### Integration

This script can be integrated into automation workflows:

```python
from scc_ai_assistant import SCCAIAssistant

# Initialize client
assistant = SCCAIAssistant(
    api_key=os.getenv('SCC_API_KEY'),
    base_url=os.getenv('SCC_REGIONAL_URL')
)

# Ask a question
response = assistant.ask("Show current device inventory")

if response:
    # Process the response
    print(f"Received: {response}")
```

#### Related Documentation

- [Getting Started Guide](../GettingStarted.md) - SCC API setup
- [FMC API Reference](.github/skills/learn_fm_api/SKILL.md) - Firewall Management Center API
- [hosts.sh.example](../hosts.sh.example) - Environment configuration template

---

### example_inventory.py

✅ **Production Ready** - Working example using the SCC Firewall Manager SDK.

Demonstrates how to use the locally installed SDK to query device inventory from Security Cloud Control.

#### Features

- ✅ Uses official SCC Firewall Manager SDK (v1.20.240)
- ✅ Clean, typed Python code with proper error handling
- ✅ Displays comprehensive device information
- ✅ Environment variable integration with hosts.sh

#### Prerequisites

1. **Python 3.7+** (required by SDK)

2. **SCC Firewall Manager SDK** - Already installed at `/home/wolfy/scc/scc-fm-sdk/`

3. **Configured hosts.sh** with required environment variables:
   - `SCC_FMC_API_KEY` - Your SCC Firewall Manager API token
   - `SCC_EDGE_URL` - SCC Firewall API endpoint

4. **Load environment variables**:
   ```bash
   set -a; source hosts.sh; set +a
   ```

#### Usage

```bash
# Load credentials
cd /home/wolfy/scc
set -a; source hosts.sh; set +a

# Run the example
python3 scripts/example_inventory.py
```

#### Example Output

```
✓ Environment configured
  Endpoint: https://api.us.security.cisco.com/firewall
  Token: eyJraWQiOi...XvwQ

📋 Fetching device inventory...

================================================================================
Device Inventory Summary
================================================================================
Total Devices: 2
Showing: 2 of 2
================================================================================

Device: asav-0
  UID: a5786fb8-b0e2-4180-9870-cc2a4767c4a7
  Type: EntityType.ASA
  Address: 10.1.141.233:8443
  State: ConnectivityState.UNREACHABLE
  Config State: ConfigState.SYNCED
  Software: 9.24(1)
  Serial: 9A1SN1K1EHQ

Device: c8000v
  UID: 4909fad2-502f-4003-aabf-119771a54a0c
  Type: EntityType.IOS
  Address: 10.1.141.201:22
  State: ConnectivityState.UNREACHABLE
  Config State: ConfigState.SYNCED
  Software: 26.01.01
  Serial: 9DKCIZHOTEE
```

#### SDK Reference

For complete SDK documentation, see:
- **Local SDK:** `/home/wolfy/scc/scc-fm-sdk/`
- **SDK Docs:** [SCC Firewall Manager SDK](#scc-firewall-manager-sdk) section below
- **Online Docs:** https://scc-firewall-manager-sdk.readthedocs.io/en/latest/
- **PyPI Package:** https://pypi.org/project/scc-firewall-manager-sdk/

#### Available SDK APIs

The SDK includes 30+ API clients:
- **InventoryApi** - Device and manager inventory
- **ObjectManagementApi** - Network objects, port lists, ACLs
- **RemoteAccessMonitoringApi** - RA VPN sessions and MFA events
- **DeviceDeploymentsApi** - Deploy configurations to devices
- **DeviceHealthApi** - Health monitoring and metrics
- **ASAAccessRulesApi** - ASA access control lists
- **ASAInterfacesApi** - ASA interface configuration
- **ChangelogsApi** - Audit trail and change history
- **TransactionsApi** - Track async operations
- **UsersApi** - User management
- And many more...

#### Extending the Example

You can modify the script to use other SDK APIs:

```python
from scc_firewall_manager_sdk.api.device_health_api import DeviceHealthApi

# Get device health
health_api = DeviceHealthApi(client)
health = health_api.get_device_health(device_uid="...")
```

See the [SDK documentation](#scc-firewall-manager-sdk) section below for complete API reference.

---

## SCC Firewall Manager SDK

The **SCC Firewall Manager SDK** (v1.20.240) is installed locally at `/home/wolfy/scc/scc-fm-sdk/` (not tracked in git).

**Installed:** 2026-06-07  
**Source:** PyPI - `scc-firewall-manager-sdk`  
**Documentation:** https://scc-firewall-manager-sdk.readthedocs.io/en/latest/

### SDK Installation

The SDK was installed using:
```bash
mkdir -p /home/wolfy/scc/scc-fm-sdk
cd /home/wolfy/scc/scc-fm-sdk
pip install --target . scc-firewall-manager-sdk
```

### SDK Contents

- **scc_firewall_manager_sdk/** - Main SDK package
  - **api/** - API client modules for all SCC FMC endpoints
  - **models/** - Pydantic models for request/response objects
  - **openapi.yaml** - OpenAPI specification (913 KB)
  - **api_client.py** - Base API client implementation
  - **configuration.py** - SDK configuration
  - **exceptions.py** - SDK exceptions

### Available API Modules

The SDK includes 30+ client modules for these APIs:

- **ai_assistant_api.py** - AI Assistant conversations (⚠️ endpoint not yet available)
- **inventory_api.py** - Device inventory management
- **object_management_api.py** - Firewall objects (networks, ports, etc.)
- **remote_access_monitoring_api.py** - RA VPN session monitoring
- **device_deployments_api.py** - Deploy configurations to devices
- **device_health_api.py** - Device health monitoring
- **asa_access_rules_api.py** - ASA access control lists
- **asa_interfaces_api.py** - ASA interface management
- **changelogs_api.py** - Audit trail and change history
- **connectors_api.py** - Secure Device Connector management
- **transactions_api.py** - Async operation tracking
- **users_api.py** - User management
- **tenant_management_api.py** - Tenant configuration
- **command_line_interface_api.py** - CLI command execution
- **device_upgrades_api.py** - Software upgrade management
- **licensing_api.py** - License management
- **search_api.py** - Search across resources
- And many more...

### Using the SDK in Your Scripts

```python
import sys
sys.path.insert(0, '/home/wolfy/scc/scc-fm-sdk')

from scc_firewall_manager_sdk import ApiClient, Configuration
from scc_firewall_manager_sdk.api.inventory_api import InventoryApi
import os

# Configure API client
config = Configuration(
    host="https://api.us.security.cisco.com/firewall",
    access_token=os.getenv('SCC_FMC_API_KEY')
)

# Create API client
client = ApiClient(configuration=config)

# Use inventory API
inventory_api = InventoryApi(client)
devices = inventory_api.get_devices()

print(f"Total devices: {devices.count}")
for device in devices.items:
    print(f"  - {device.name} ({device.device_type})")
```

### Example: Using AI Assistant API

The AI Assistant API is included in the SDK but the endpoint is not yet available in production:

```python
from scc_firewall_manager_sdk.api.ai_assistant_api import AIAssistantApi
from scc_firewall_manager_sdk.models.ai_question import AiQuestion

# Create AI Assistant API client
ai_api = AIAssistantApi(client)

# Ask a question (will work once endpoint is available)
question = AiQuestion(content="How many devices are managed?")
conversation = ai_api.ask_ai_assistant(ai_question=question)
```

### SDK Dependencies

The SDK requires:
- pydantic >= 2.0
- python-dateutil
- typing-extensions >= 4.7.1
- urllib3 < 2.1.0

All dependencies are included in the local installation.

### OpenAPI Specification

The full OpenAPI specification is available at:
`/home/wolfy/scc/scc-fm-sdk/scc_firewall_manager_sdk/openapi.yaml`

This can be used with OpenAPI tools to generate documentation, mock servers, or clients in other languages.

---

## Contributing

When adding new scripts:

1. Include proper docstrings and type hints
2. Use environment variables from hosts.sh
3. Add error handling and user feedback
4. Update this README with usage instructions
5. Make scripts executable: `chmod +x script.py`
