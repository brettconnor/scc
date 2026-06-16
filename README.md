# SCC Agent Harness Workspace

VS Code Copilot workspace for Cisco Security Cloud Control with two specialized agents:

1. **SCC Admin** (@SCC) - User/group/role management and org administration
2. **FMC** (@FMC) - Firewall device management, policies, objects, and VPN

Combines MCP-based discovery with deterministic SDK writes, reusable scripts, and CodeGuard security review.

## Repository Layout

| Path | Purpose |
|---|---|
| **SCC Admin** | |
| .github/agents/security-cloud-control.agent.md | Agent definition |
| .github/skills/scc/ | Credentials, MCP, API utilities |
| .github/skills/scc_hybrid/ | Hybrid MCP + SDK wrapper |
| .github/skills/scc_codegen/ | Script generation & CodeGuard |
| scc-sdk/ | Local SDK for writes |
| **FMC** | |
| .github/agents/scc-firewall-manager.agent.md | Agent definition |
| .github/skills/scc_fm/ | API connectivity & device discovery |
| .github/skills/scc_fm_hybrid/ | Hybrid MCP + SDK wrapper |
| .github/skills/scc_fm_codegen/ | Script generation & CodeGuard |
| .github/skills/learn_fm_api/ | API reference docs |
| scc-fm-sdk/ | Local SDK v1.20.240 |
| **Shared** | |
| .vscode/ | MCP server config |
| codeguard/ | Security rules & review |
| scripts/ | Utility scripts |

## VS Code Workspace MCP Files

`.vscode/mcp.json` declares the `security-cloud-control` MCP endpoint (reads `SCC_API_KEY`).  
`.vscode/settings.json` scopes workspace MCP sampling.

These files control local editor behavior only. By default `.vscode/` is gitignored.

## Submodules

```bash
# Initialize after cloning
git submodule update --init --recursive

# Refresh to configured branches
git submodule update --remote --recursive
```

## Quick Start

### 1) Configure credentials

```bash
cp hosts.sh.example hosts.sh
# Edit hosts.sh with your values
```

**SCC Admin**: `SCC_API_KEY`, `SCC_API_KEY_ID`, `SCC_ORG_ID`, `SCC_ORG_UUID`, `SCC_URL`  
**FMC**: `SCC_FMC_API_KEY`, `SCC_EDGE_URL`, `SCC_ORG_UUID`

### 2) Run bootstrap

```bash
# SCC Admin
bash .github/skills/scc_hybrid/bootstrap.sh

# FMC
bash .github/skills/scc_fm_hybrid/bootstrap.sh
```

### 3) Run connectivity checks

```bash
# SCC Admin
bash .github/skills/scc/check_mcp.sh
bash .github/skills/scc/check_api_scopes.sh

# FMC
bash .github/skills/scc_fm/check_fmc_api.sh
bash .github/skills/scc_fm/get_devices.sh
```

## Environment Pattern

```bash
set -a; source hosts.sh; set +a && <command>
```

## Hybrid Operating Model

Both agents use staged execution:
1. **Discovery** (MCP): Resolve context
2. **Planning**: Summarize impact, request confirmation
3. **Execution** (SDK/REST): Deterministic writes
4. **Verification**: Confirm final state

Write operations require readiness gates and explicit approval.

## Core Skills

**SCC Admin**: scc, scc_hybrid, scc_codegen  
**FMC**: scc_fm, scc_fm_hybrid, scc_fm_codegen, learn_fm_api

See `.github/skills/*/SKILL.md` for documentation.

## Security

- Keep credentials in local `hosts.sh` only
- Require confirmation before write operations
- Run CodeGuard review before delivering generated scripts
- Prefer dry-run and verification for bulk workflows

## Token Lifecycle

API tokens expire based on org policy. When auth fails:
1. Generate new API key in SCC UI
2. Update `SCC_API_KEY`/`SCC_REFRESH_KEY`/`SCC_API_KEY_ID` or `SCC_FMC_API_KEY` in hosts.sh
3. Rerun connectivity checks

## Common Commands

```bash
# SCC Admin
bash .github/skills/scc_hybrid/bootstrap.sh
bash .github/skills/scc/check_mcp.sh
bash .github/skills/scc/check_api_scopes.sh

# FMC
bash .github/skills/scc_fm_hybrid/bootstrap.sh
bash .github/skills/scc_fm/check_fmc_api.sh
bash .github/skills/scc_fm/get_devices.sh
```

## License

This repository is licensed under Apache License 2.0. See [LICENSE](LICENSE).

## Third-Party Licenses

- scc-sdk is licensed under Apache License 2.0: [scc-sdk/LICENSE](scc-sdk/LICENSE)
- codeguard is licensed under CC BY 4.0: [codeguard/LICENSE.md](codeguard/LICENSE.md)

## Related Docs

- **SCC Admin**: [Agent](.github/agents/security-cloud-control.agent.md) | [Skills](.github/skills/scc/)
- **FMC**: [Agent](.github/agents/scc-firewall-manager.agent.md) | [Skills](.github/skills/scc_fm/) | [API Ref](.github/skills/learn_fm_api/)
- **Setup**: [GettingStarted.md](GettingStarted.md)
