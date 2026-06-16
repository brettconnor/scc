---
name: scc
description: Security Cloud Control authentication and MCP connection utilities. Provides credential loading from hosts.sh and an interactive tool for testing MCP server connectivity.
---

# Security Cloud Control Utilities Skill

This skill provides utilities for connecting to Cisco Security Cloud Control via MCP (Model Context Protocol), with authentication credential management and token refresh support.

## When to Use This Skill

- Testing MCP server connectivity and tool discovery
- Troubleshooting SCC authentication issues
- Discovering available SCC API tools
- Manual testing of SCC MCP tools
- Debugging MCP integration problems

## What This Skill Provides

### Files in `.github/skills/scc/`

All scripts require only `curl` and `python3` (stdlib) — no venv or pip install needed.

1. **check_mcp.sh** - MCP connectivity test and tool inventory report
   - Initializes an MCP session and reports server name/version/protocol
   - Lists all available `platform_management_*` tools grouped by category
   - Prints `RESULT: PASS` / `FAIL` summary
   - Usage: `bash .github/skills/scc/check_mcp.sh`

2. **get_scc_org.sh** - List SCC organizations
   - Calls `GET /organizations` with the bearer token from `hosts.sh`
   - Returns org UUID, name, region, and type as JSON
   - Usage: `bash .github/skills/scc/get_scc_org.sh`

3. **check_api_scopes.sh** - API key scope and permission analyzer
   - Decodes JWT token and displays claims (org ID, user type, etc.)
   - Tests connectivity to REST API, MCP, and objects endpoints
   - Shows which capabilities are available with current key
   - Reports missing scopes for restricted endpoints
   - Usage: `bash .github/skills/scc/check_api_scopes.sh`

4. **test_sdk.py** - SDK connectivity test (requires SDK installation)
   - Tests Python SDK with local installation at `/home/wolfy/scc/scc-sdk/`
   - Validates SDK imports (Client, exceptions)
   - Makes sample API call to verify connectivity
   - Usage: `python3 .github/skills/scc/test_sdk.py`

5. **scc.py** - Interactive MCP REPL (Python 3.9+ stdlib only)
   - Connects to SCC MCP server and lists available tools
   - Interactive `call <tool> <json_args>` loop for manual tool testing
   - No venv or external dependencies required
   - Usage: `python3 .github/skills/scc/scc.py`

## Quick Start

No installation required. All scripts source `hosts.sh` automatically.

**Token Management**: Token lifetimes vary by org policy and key type. When authentication fails or a key nears expiry, generate a new API key in the SCC UI (Settings → API Keys), then update `SCC_API_KEY`, `SCC_REFRESH_KEY`, and `SCC_API_KEY_ID` in `hosts.sh`.

### Configuration

Credentials are sourced automatically from `hosts.sh` at the repo root:

```
SCC_API_KEY       — Bearer token for API authentication
SCC_ORG_ID        — Organization display name (e.g. "Cisco STO GCT DP")
SCC_API_KEY_ID    — API key UUID
SCC_REFRESH_KEY   — Refresh token (stored but not used — SCC refresh endpoint is non-functional)
SCC_URL           — Base REST API URL
```

> **Note**: `SCC_ORG_ID` is the display name; scripts that need the org UUID resolve it
> dynamically via `GET /organizations`.

### Test MCP connectivity

```bash
bash .github/skills/scc/check_mcp.sh
```

Expected: MCP session initialized, 21 tools listed, `RESULT: PASS`.

### List organizations (get org UUID)

```bash
bash .github/skills/scc/get_scc_org.sh
```

### Check API key scopes and endpoint access

```bash
bash .github/skills/scc/check_api_scopes.sh
```

Shows JWT claims, which endpoints are accessible, and what scopes are needed for restricted endpoints.

## Architecture

```
check_mcp.sh / get_scc_org.sh / check_api_scopes.sh
    └── curl → SCC REST API / MCP Server → Security Cloud Control
```

All bash scripts:
1. Source `hosts.sh` from the repo root for credentials
2. Make direct `curl` calls with `Bearer` auth
3. Parse responses with `python3` stdlib (`json.tool` / `json.load`)

## Key Features

- **No dependencies**: Only `curl` and `python3` stdlib — works on any macOS/Linux host
- **Credential-free setup**: Automatically loads from `hosts.sh`
- **MCP tool discovery**: `check_mcp.sh` lists all available SCC platform management tools
- **Org introspection**: `get_scc_org.sh` returns the org UUID needed for other API calls

## Token Lifecycle

SCC key lifetimes vary by org policy and key type. If token refresh is unavailable or fails for your org, use **manual key rotation**.

### When Your Token Expires
1. Visit https://security.cisco.com → **Settings → API Keys**
2. Generate a new API key for `Cisco STO GCT DP`
3. Using the **Copy buttons** in the UI (do not drag-select), copy both tokens
4. Update `hosts.sh`:
   ```
   SCC_API_KEY_ID   ← Key ID field
   SCC_API_KEY      ← Access Token (use Copy button)
   SCC_REFRESH_KEY  ← Refresh Token (use Copy button)
   ```
5. Verify with `bash .github/skills/scc/get_scc_org.sh`

> **Important**: Always use the UI Copy buttons — the token values are truncated in the visible display.

## Use Cases

| Task | Script |
|------|--------|
| Test MCP connectivity | `bash check_mcp.sh` |
| Discover available tools | `bash check_mcp.sh` |
| Get org UUID | `bash get_scc_org.sh` |
| Decode JWT / check scopes | `bash check_api_scopes.sh` |
| Test Python SDK | `python3 test_sdk.py` |
| Expired token | Manual rotation — see Token Lifecycle above |

## Integration with VS Code Agent

This skill complements the [security-cloud-control VS Code agent](../../agents/security-cloud-control.agent.md):

| Use Case | VS Code Agent | This Utility |
|----------|---------------|--------------|
| Interactive agent queries | ✅ Best choice | ❌ |
| Manual tool testing | ❌ | ✅ Best choice |
| Tool discovery | ❌ | ✅ Best choice |
| Troubleshooting MCP | ❌ | ✅ Best choice |
| Automation workflows | ✅ Best choice | ❌ |

## Troubleshooting

### Token Expired (Manual Regeneration Required)

**Symptom**: `scc.py` displays "SCC API Token EXPIRED" error

**Cause**: Access and refresh tokens are both expired, revoked, or no longer valid

**Solutions**:
1. Visit: https://security.cisco.com
2. Navigate: Settings → API Keys
3. Delete the old expired key
4. Generate new API key for "Cisco STO GCT DP"
5. Update `hosts.sh` with BOTH values from the response:
   - `access_token` → `SCC_API_KEY`
   - `refresh_token` → `SCC_REFRESH_KEY`

### Token Refresh Returns `"refresh token is not valid"`

**Symptom**: `auto-refresh-if-needed.sh` displays "Refresh Token Invalid" error

**Cause**: Refresh token has expired or been invalidated (happens when tokens go unused for extended periods)

**Solutions**:
- Same as "Token Expired" above — regenerate API key in SCC console
- Update both `SCC_API_KEY` and `SCC_REFRESH_KEY` in `hosts.sh`

### Connection Issues

**Symptom**: `FAIL — HTTP <no response>` or `FAIL — Empty response`

**Solutions**:
- Verify `SCC_API_KEY` is valid and not expired in `hosts.sh`
- Run `python3 .github/skills/scc/scc.py` — auto-refresh will run if token is expiring
- Check network connectivity to `mcp.security.cisco.com`

### Auto-Refresh Lock Timeout

**Symptom**: `auto-refresh-if-needed.sh` returns "Could not acquire lock after 30s"

**Cause**: Another `scc.py` or refresh script instance is currently refreshing tokens

**Solutions**:
- Wait 30 seconds and retry
- Check for stuck processes: `ps aux | grep auto-refresh`
- Remove stale lockfile if no process is running: `rm .github/skills/scc/.token-refresh.lock`

### Missing Credentials

**Symptom**: `ERROR: SCC_API_KEY not set in hosts.sh`

**Solutions**:
- Ensure `hosts.sh` exists at the repo root
- Verify the required SCC variables are set in `hosts.sh`
- Test manually: `source hosts.sh && echo "${SCC_API_KEY:0:8}..."`

### Skip Auto-Refresh

**Symptom**: Need to test with current token without auto-refresh

**Solutions**:
- Run: `python3 .github/skills/scc/scc.py --skip-refresh`
- Useful for debugging token issues or testing with known-expired tokens

## Related Files

- VS Code Agent: [../../agents/security-cloud-control.agent.md](../../agents/security-cloud-control.agent.md)
- VS Code MCP config: [.vscode/mcp.json](../../../.vscode/mcp.json)
- Agent Registry: [AGENTS.md](../../../AGENTS.md)

## Support

For issues with:
- **MCP connectivity**: Run `bash check_mcp.sh` — it will report `PASS`/`FAIL` with details
- **Token expiration**: Run `python3 .github/skills/scc/scc.py` to validate status and attempt refresh if supported
- **Refresh unavailable/invalid**: Follow "Token Expired" troubleshooting steps above
- **Credentials**: Validate `hosts.sh` has `SCC_API_KEY`, `SCC_API_KEY_ID`, `SCC_REFRESH_KEY`, `SCC_URL`
- **Architecture**: Review [SCC documentation](https://www.cisco.com/site/us/en/products/networking/cloud-networking-services/security/security-cloud-control/index.html)
