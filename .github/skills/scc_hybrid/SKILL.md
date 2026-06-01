---
description: "Hybrid MCP discovery + deterministic SDK write wrapper for SCC Admin workflows"
hints:
  - "Use when executing SCC write operations (invite, create, assign) that require both discovery context and mutation"
  - "Provides pre-scoped write wrappers for users, groups, and roles — no need to pass org_id explicitly"
  - "Intent routing automatically classifies operations as WRITE (sdk) or DISCOVER (mcp) to coordinate MCP + SDK execution"
  - "Session cache prevents redundant API calls for name→UUID lookups within one workflow cycle"
  - "Error recovery enforces MCP verify → compensate → operator guidance precedence"
  - "Startup gates verify credentials, MCP connectivity, API scope, and org binding before any operation"
---

# SCC Hybrid Skill

Provides a thin Python wrapper over the read-only `scc-sdk` sub-repo, combining MCP discovery with deterministic SDK writes in one context manager for use by the SCC Admin agent.

## When to Use This Skill

- When the SCC Admin agent needs to execute write operations (invite, create group, assign role)
- When wiring MCP discovery results into SDK execution calls
- When building onboarding workflows that mix context (MCP) with mutation (SDK)
- When debugging or testing SCC write operations independently of the agent

## Files

| File | Purpose |
|------|---------|
| `scc_hybrid_context.py` | Thin wrapper context manager — delegates to `scc-sdk/scc_sdk/resources` |
| `bootstrap.sh` | One-command preflight: dependency install, hosts.sh export, and smoke test |

## Architecture

```
SCC Admin Agent
    │
    ├── MCP tools (security-cloud-control/*)   ← Discovery / context / NLP reads
    │
    └── scc_hybrid_context.py                  ← Deterministic writes
            │
            └── scc-sdk/scc_sdk/resources/     ← NOT modified — read-only sub-repo
                    ├── organizations.py
                    ├── users.py
                    ├── groups.py
                    └── roles.py
```

## Quick Start

### One-command bootstrap (recommended)

```bash
bash .github/skills/scc_hybrid/bootstrap.sh
```

This command:
- installs `scc-sdk` Python requirements when missing
- falls back to `https://pypi.org/simple` if your default index cannot resolve packages
- exports variables from `hosts.sh` for child processes
- runs the safe hybrid smoke test

### 0) Bootstrap Python dependencies (required)

The hybrid context imports `scc-sdk`, which requires Python packages from `scc-sdk/requirements.txt`.

```bash
python3 -m pip install -r scc-sdk/requirements.txt
```

If your environment is pinned to an internal index that does not mirror `requests`, use a one-off fallback:

```bash
PIP_INDEX_URL=https://pypi.org/simple python3 -m pip install -r scc-sdk/requirements.txt
```

### 1) Export credentials to Python process (CRITICAL)

**⚠️ IMPORTANT**: Environment variables must be sourced BEFORE invoking Python. Do not rely on `source hosts.sh` alone inside the Python script; the hybrid context gates read from the parent shell environment.

#### Standard Pattern (Option 1 — Recommended)

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

#### Example: List active users (Option 1)

```bash
set -a; source hosts.sh; set +a && python3 << 'EOF'
import sys
sys.path.insert(0, ".github/skills/scc_hybrid")
from scc_hybrid_context import SCCHybridContext

with SCCHybridContext() as ctx:
    users_response = ctx.users.list(ctx.org_id)
    users = users_response.get('users', [])
    active_users = [u for u in users if u.get('status') == 'ACTIVE']
    
    for user in active_users:
        print(f"{user['email']:<35} {user['fullName']:<25} {user['status']:<10}")
    
    print(f"\nTotal active: {len(active_users)} / {len(users)}")
EOF
```

### 2) Use the context manager

```python
import sys, os
sys.path.insert(0, ".github/skills/scc_hybrid")
from scc_hybrid_context import SCCHybridContext, OperationIntent

with SCCHybridContext() as ctx:
    # Read path — delegate to MCP tools in the agent, or call SDK directly:
    users = ctx.users.list(ctx.org_id)

    # Classify and route intent:
    intent = ctx.classify_intent("invite john@example.com")
    # → OperationIntent.WRITE  →  route: "sdk"

    # Write path — after operator confirmation:
    ctx.invite_user("john@example.com", "John", "Doe")
    ctx.create_group("Network Team")
    ctx.add_user_to_group(group_id, "john@example.com")
    role_id = ctx.find_role_id("Organization Administrator")
    ctx.assign_role_to_user(role_id, user_id)
```

### Reusable Workflow Scripts

Reusable workflow templates are owned by the `scc_codegen` skill.

- Canonical template: `.github/skills/scc_codegen/script_template.sh`
- Use `scc_hybrid` for runtime context and deterministic wrappers
- Use `scc_codegen` when generating or maintaining reusable workflow scripts

## Startup Gates

The context manager enforces 4 gates on `__enter__`:

| # | Gate | Script / Method | Blocks on failure |
|---|------|-----------------|-------------------|
| 1 | Credentials | env var check | All operations |
| 2 | MCP connectivity | `check_mcp.sh` → `RESULT: PASS` | All operations |
| 3 | API scope | `check-api-scopes.sh` → ✓ /organizations | All operations |
| 4 | Org binding | `SDK organizations.list()` → match `$SCC_ORG_ID` | All operations |

## SDK Resource Pass-Throughs

Direct access to all `scc-sdk` resource methods via properties:

```python
ctx.users.list(ctx.org_id)
ctx.users.get(ctx.org_id, user_id)
ctx.groups.list(ctx.org_id)
ctx.groups.get_assigned_roles(ctx.org_id, group_id)
ctx.roles.list(ctx.org_id)
ctx.roles.find_role_id(ctx.org_id, product_name, display_name)
ctx.organizations.list()
```

## Thin Write Wrappers

Pre-scoped to `$SCC_ORG_ID` — no need to pass `org_id` explicitly:

| Method | SDK call |
|--------|----------|
| `invite_user(email, first, last)` | `users.invite(org_id, ...)` |
| `disable_user(email)` | `users.disable(org_id, email)` |
| `enable_user(email)` | `users.enable(org_id, email)` |
| `remove_user(email)` | `users.remove(org_id, email)` |
| `update_user(user_id, first, last)` | `users.update(org_id, ...)` |
| `create_group(name, description)` | `groups.create(org_id, name, description)` ¹ |
| `delete_group(group_id)` | `groups.delete(org_id, group_id)` |
| `add_user_to_group(group_id, email)` | `groups.patch(org_id, group_id, users=[add])` |
| `remove_user_from_group(group_id, email)` | `groups.patch(org_id, group_id, users=[remove])` |
| `assign_role_to_user(role_id, user_id)` | `roles.patch(org_id, role_id, users=[add])` |
| `assign_role_to_group(role_id, group_id)` | `roles.patch(org_id, role_id, groups=[add])` |
| `find_role_id(display_name)` | `roles.find_role_id(org_id, product, name)` + cache |

> ¹ `create_group` **never** passes `appliesTo` — this field causes API failures.

## Intent Routing

```python
intent = ctx.classify_intent("invite alice@example.com")
# → OperationIntent.WRITE  (route: "sdk")

intent = ctx.classify_intent("list all users")
# → OperationIntent.DISCOVER  (route: "mcp")

route = ctx.route_operation(intent)
# → "sdk" or "mcp"
```

**Write keywords**: create, invite, add, assign, update, delete, remove, patch, onboard, disable, enable, grant, revoke  
**Discover keywords**: list, show, find, search, audit, report, get

## Error Recovery

`handle_sdk_failure(error, operation)` enforces the recovery precedence:

1. **MCP verify** — re-read affected state to detect partial success or drift
2. **Compensate** — corrective action if partial success detected  
3. **Operator guidance** — actionable message + `retry` flag

SDK exception → guidance mapping:

| Exception | HTTP | `retry` | Guidance |
|-----------|------|---------|---------|
| `AuthenticationError` | 401 | `False` | Rotate token in hosts.sh |
| `ForbiddenError` | 403 | `False` | Verify Organization Admin role |
| `NotFoundError` | 404 | `False` | Verify org/user/group/role IDs |
| `ValidationError` | 400 | `True` | Review request parameters |
| `ServerError` | 5xx | `True` | Transient — wait and retry |

## Session Cache

Cache lifetime = one workflow cycle (one `with` block).

The context manager automatically caches name→UUID lookups:
- Write wrappers populate cache after success
- `find_role_id()` caches role lookups  
- Cache is cleared when context exits (fresh start for next workflow)

```python
with SCCHybridContext() as ctx:
    role_id = ctx.find_role_id("Organization Administrator")  # API call → cached
    ctx.assign_role_to_user(role_id, user_1)                  # uses cached role_id ✓
    ctx.assign_role_to_user(role_id, user_2)                  # uses cached role_id ✓
    # No redundant API calls
```

**Manual control (optional):**
```python
ctx.get_cached("roles", "Organization Administrator")  # peek at cache
ctx.clear_cache("roles")                               # force fresh reads
ctx.clear_cache()                                      # clear all
```

## Credential Requirements

All sourced from `hosts.sh` at the repo root:

| Variable | Purpose |
|----------|---------|
| `SCC_API_KEY` | Bearer token for API authentication |
| `SCC_ORG_ID` | Organization display name |
| `SCC_ORG_UUID` | Organization UUID |
| `SCC_API_KEY_ID` | API key UUID |
| `SCC_URL` | Base REST API URL |

Token lifetimes vary by org policy and key type. If refresh is unavailable or fails in your org, rotate keys manually via SCC UI (Settings → API Keys).

## Installation and Index Troubleshooting

- Symptom: `Missing environment variables: SCC_API_KEY ...`
- Cause: Environment variables are not exported to the Python process
- Fix: Use the standard pattern: `set -a; source hosts.sh; set +a && python3 script.py`
- Why: `source hosts.sh` sets shell variables, but child processes only inherit exported variables. The hybrid context gates check process environment variables at startup.

- Symptom: `ModuleNotFoundError: No module named 'requests'`
- Cause: `scc-sdk` dependencies are not installed in the active Python environment
- Fix: `python3 -m pip install -r scc-sdk/requirements.txt`

- Symptom: `No matching distribution found for requests>=2.25.0`
- Cause: active pip index does not mirror required packages
- Fix: use `PIP_INDEX_URL=https://pypi.org/simple` for bootstrap or update internal mirror config

## Related

- Agent: [../../agents/security-cloud-control.agent.md](../../agents/security-cloud-control.agent.md)
- SCC utilities skill: [../scc/SKILL.md](../scc/SKILL.md)
- SDK source (read-only): [../../../scc-sdk/scc_sdk/resources](../../../scc-sdk/scc_sdk/resources)
