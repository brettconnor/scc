---
name: scc_fm_codegen
description: Detects FMC workflow requests that should be implemented as one-shot SDK scripts and provides CodeGuard security review guidance before code handoff.
---

# FMC Workflow Script Planning and Secure Codegen Skill

Use this skill when FMC operators ask for repeatable workflows, especially bulk device operations, policy deployments, or object management across multiple devices or configurations.

## When to Use

Activate this skill when one or more are present:
- Multi-device operations with repeated patterns
- Bulk device onboarding or configuration
- Multi-device policy deployment
- Repeated object creation (networks, services, rules)
- Cross-device configuration synchronization
- Operator asks for reusable automation or scheduled operations
- Requirement for dry-run, idempotency, rollback, or audit reports

## Files

| File | Purpose |
|------|---------|
| `script_template.sh` | Canonical reusable FMC workflow template with preflight checks, SDK setup, and exported `hosts.sh` environment pattern |

## Reusable Workflow Template

Use this skill-owned template when creating repeatable FMC workflows:

```bash
cp .github/skills/scc_fm_codegen/script_template.sh fmc_workflow.sh
# Then edit the PYTHON CODE SECTION in fmc_workflow.sh
bash fmc_workflow.sh
```

The template automatically:
- ✓ Checks for Python and `hosts.sh`
- ✓ Sets up FMC SDK path
- ✓ Exports environment variables correctly (`set -a; source hosts.sh; set +a`)
- ✓ Provides starter code with documented FMC API examples

## Required Behavior

1. Detect workflow intent and classify as a Script Candidate Workflow.
2. Propose a one-shot script plan before making mutation calls.
3. Ask for approval on the plan before generating code.
4. If approved, generate deterministic SDK-based code with clear stages.
5. Include CodeGuard security review guidance notes with final code handoff.

## Script Plan Template

Every plan should include:
1. **Scope**: Devices, policies, objects affected; estimated impact count
2. **Input Contract**: CSV/JSON schema for device lists, object definitions, etc.
3. **Preflight Gates**:
   - Credentials gate (SCC_FMC_API_KEY, SCC_EDGE_URL)
   - API access validation
   - Resource existence verification (devices, cdFMC)
   - SDK installation check
4. **Dry-Run Behavior**: Show planned actions without executing
5. **Execution Stages**: 
   - Stage 1: Discovery (query devices, objects, policies)
   - Stage 2: Validation (check prerequisites)
   - Stage 3: Mutation (create/update operations)
   - Stage 4: Deployment (if needed)
   - Stage 5: Transaction tracking (async operations)
6. **Verification Checks**: Post-write API reads to confirm changes
7. **Rollback Strategy**: Undo path for partial failures
8. **Audit Artifact**: Machine-readable log with timestamps, UIDs, and status

## FMC-Specific Workflow Patterns

### Pattern 1: Bulk Device Onboarding
```
Input:  CSV with device IPs, credentials, device types
Steps:  1. Validate connectivity to each device
        2. Check for existing devices (avoid duplicates)
        3. Create device records
        4. Monitor onboarding transactions
Output: Device UIDs, onboarding status, failed devices
```

### Pattern 2: Policy Deployment
```
Input:  Device UIDs or names, policy changes
Steps:  1. Discover target devices
        2. Validate policy syntax
        3. Apply policy changes
        4. Deploy to devices
        5. Track deployment transactions
Output: Deployment status, transaction IDs, errors
```

### Pattern 3: Object Management
```
Input:  Network object definitions (YAML/JSON)
Steps:  1. Check for existing objects (avoid duplicates)
        2. Create network objects
        3. Create port objects
        4. Create object groups
        5. Verify creation
Output: Object UIDs, creation status, audit log
```

## SDK vs Direct API Guidance

**Prefer SDK when:**
- Python script automation
- Need type checking and IDE support
- Complex workflows with multiple API calls
- Want structured request/response handling

**Use direct API (curl) when:**
- Quick exploratory scripts
- Shell-based automation
- SDK doesn't support endpoint yet
- Debugging or testing

## Security Review Guidance

Before returning new or modified code, consider:

1. **Baseline skill**:
   - `codeguard/skills/software-security/SKILL.md`

2. **Always-on rules**:
   - `codeguard-1-hardcoded-credentials.md` - No hardcoded tokens or passwords
   - `codeguard-1-crypto-algorithms.md` - Secure crypto usage
   - `codeguard-1-digital-certificates.md` - Proper cert validation

3. **Language-specific rules**:
   - Apply Python security rules from CodeGuard skill
   - Shell script security (input validation, quoting)

4. **FMC-Specific Security Considerations**:
   - Never log API tokens in output
   - Sanitize device credentials in logs
   - Validate device IP addresses before connections
   - Check certificate validation is enabled
   - Secure storage of device passwords
   - Audit trail for all write operations

5. **Output requirement**:
   - Include a Security Review Note with:
     - Security checks considered
     - Findings and mitigations
     - Residual risk notes
     - Recommendations for secure deployment

If security review is skipped or deferred, include a brief note explaining why and suggest next steps.

## FMC-Specific Guardrails

- **Discovery first**: Use MCP or SDK to discover devices/objects before writes
- **Transaction tracking**: For async operations, always track transaction UIDs
- **Idempotency**: Check for existing resources before creating duplicates
- **Error handling**: Wrap API calls in try/except with specific error types
- **Rate limiting**: Respect API rate limits for bulk operations
- **Dry-run mode**: Always implement `--dry-run` flag for testing
- **Audit logging**: Log all mutation operations with timestamps and UIDs
- **Rollback support**: Document manual rollback steps for each operation

## Code Generation Patterns

### Environment Variable Loading
```python
import os

# Required environment variables
SCC_FMC_API_KEY = os.getenv('SCC_FMC_API_KEY')
SCC_EDGE_URL = os.getenv('SCC_EDGE_URL')

if not SCC_FMC_API_KEY or not SCC_EDGE_URL:
    print("✗ Missing required environment variables")
    print("  Run: set -a; source hosts.sh; set +a")
    sys.exit(1)
```

### SDK Client Setup
```python
import sys
sys.path.insert(0, '/home/wolfy/scc/scc-fm-sdk')

from scc_firewall_manager_sdk import ApiClient, Configuration
from scc_firewall_manager_sdk.api.inventory_api import InventoryApi

config = Configuration(
    host=SCC_EDGE_URL,
    access_token=SCC_FMC_API_KEY
)
client = ApiClient(configuration=config)
```

### Error Handling
```python
try:
    inventory_api = InventoryApi(client)
    devices = inventory_api.get_devices()
except Exception as e:
    print(f"✗ API call failed: {e}")
    sys.exit(1)
```

### Dry-Run Pattern
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true', help='Show planned actions without executing')
args = parser.parse_args()

if args.dry_run:
    print("DRY RUN MODE - No changes will be made")
    print(f"Would create network object: {network_name}")
else:
    # Actual API call
    result = api.create_network_object(network_data)
```

## Example Workflow Triggers

These requests should trigger script planning:

1. "Onboard 50 ASA devices from this CSV file"
2. "Deploy this access policy to all FTD devices"
3. "Create network objects for all branch office subnets"
4. "Update NAT rules across 20 devices"
5. "Generate weekly device health reports"
6. "Synchronize security zones across all devices"
7. "Bulk update device passwords"
8. "Deploy configuration changes to devices in staging environment"

## Integration with FMC Agent

This skill complements the FMC agent by:
- Detecting when interactive operations should become scripts
- Providing script templates for approved workflows
- Enforcing security review before code handoff
- Standardizing credential and error handling patterns

The FMC agent should:
1. Detect script candidate workflows automatically
2. Propose this skill for planning
3. Use generated scripts for repeatable operations
4. Track audit trails from script executions
