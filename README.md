# SCC Agent Workspace

This repository contains the Security Cloud Control (SCC) agent workspace used to design, test, and operationalize SCC administration workflows.

The workspace combines:
- MCP-based discovery and read-heavy operations
- Deterministic SDK-style write execution for safe mutations
- Reusable script patterns for repeatable workflows
- CodeGuard security review guidance for generated automation

## What This Repo Is For

Use this repo when you need to:
- onboard/offboard SCC users
- create and manage groups
- assign or revoke roles
- run org-scoped audits and access reviews
- build repeatable SCC workflow scripts

## Repository Layout

Top-level components:

| Path | Purpose |
|---|---|
| `.github/agents/security-cloud-control.agent.md` | SCC Admin agent definition and operating policy |
| `.github/skills/scc/` | Credential, MCP connectivity, and API scope utilities |
| `.github/skills/scc_hybrid/` | Hybrid MCP + SDK wrapper and preflight bootstrap |
| `.github/skills/scc_codegen/` | Workflow-to-script escalation and secure codegen guidance |
| `scc-sdk/` | Local SCC SDK implementation used by hybrid write paths |
| `codeguard/` | Security rules, reviewer docs, and secure coding skill assets |
| `pyagent/` | Python agent experiments and local tests |

## Submodules

This repo uses git submodules for `codeguard`, `scc-sdk`, and `pyagent`.

After cloning, initialize and update submodules:

```bash
git submodule update --init --recursive
```

To refresh submodules to their configured branches:

```bash
git submodule update --remote --recursive
```

## Quick Start

### 1) Configure credentials

Create your local credentials file from the safe template:

```bash
cp hosts.sh.example hosts.sh
```

Edit `hosts.sh` and provide valid SCC values for at least:
- `SCC_API_KEY`
- `SCC_API_KEY_ID`
- `SCC_ORG_ID`
- `SCC_ORG_UUID`
- `SCC_URL`

### 2) Run hybrid bootstrap (recommended)

```bash
bash .github/skills/scc_hybrid/bootstrap.sh
```

This performs dependency checks, loads `hosts.sh`, validates readiness, and runs a hybrid smoke test.

### 3) Run SCC connectivity checks

```bash
bash .github/skills/scc/check_mcp.sh
bash .github/skills/scc/check-api-scopes.sh
bash .github/skills/scc/get_scc_org.sh
```

## Environment Pattern

For one-liners and scripts, export from `hosts.sh` into child processes with:

```bash
set -a; source hosts.sh; set +a && <your_command_here>
```

This ensures Python and shell child processes can access required SCC variables.

## Hybrid Operating Model

The SCC Admin flow in this repo uses a staged model:

1. Discovery phase (MCP path): resolve users, groups, roles, and org context.
2. Planning phase (agent policy): summarize impact and request confirmation.
3. Execution phase (SDK path): perform deterministic writes (invite/create/assign/remove).
4. Verification phase (MCP or SDK read-back): confirm final state and report IDs/status.

Write operations should not run until readiness gates pass and explicit approval is present.

## Core Skills

### SCC utility skill

`.github/skills/scc/SKILL.md` provides:
- MCP session readiness checks
- org discovery
- API scope introspection
- interactive MCP utility script

### SCC hybrid skill

`.github/skills/scc_hybrid/SKILL.md` provides:
- `SCCHybridContext` wrapper for deterministic writes against `scc-sdk`
- startup gates (credentials, MCP, scope, org binding)
- intent routing guidance (discover vs write)
- cache and error recovery patterns

### SCC codegen skill

`.github/skills/scc_codegen/SKILL.md` provides:
- script-candidate workflow detection
- one-shot workflow planning template
- reusable script template for repeatable operations
- CodeGuard security review requirements before handoff

## Security and Safety Expectations

- Do not commit real tokens or secrets.
- Keep credentials only in local `hosts.sh`.
- Require confirmation before write operations.
- Run CodeGuard-aligned review before delivering generated scripts.
- Prefer dry-run and verification steps for bulk workflows.

## Token Lifecycle Notes

SCC API token lifetimes can vary by org policy and key type. Rotate keys through the SCC UI when authentication fails or when keys near expiry.

If authentication fails:
- generate a new API key in SCC
- update `SCC_API_KEY`, `SCC_REFRESH_KEY`, and `SCC_API_KEY_ID` in `hosts.sh`
- rerun connectivity checks

## Common Commands

```bash
# Hybrid bootstrap + smoke test
bash .github/skills/scc_hybrid/bootstrap.sh

# Check MCP connectivity
bash .github/skills/scc/check_mcp.sh

# Inspect API scopes and endpoint access
bash .github/skills/scc/check-api-scopes.sh

# List accessible organizations
bash .github/skills/scc/get_scc_org.sh
```

## Related Docs

- Agent definition: `.github/agents/security-cloud-control.agent.md`
- SCC skill docs: `.github/skills/scc/SKILL.md`
- Hybrid skill docs: `.github/skills/scc_hybrid/SKILL.md`
- Script/codegen docs: `.github/skills/scc_codegen/SKILL.md`
- Operator notes: `OperatorNotes.md`
