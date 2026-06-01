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

```python
import sys, os
sys.path.insert(0, ".github/skills/scc_hybrid")
from scc_hybrid_context import SCCHybridContext, OperationIntent

# source hosts.sh first, then:
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

The context manager caches name→UUID lookups in memory for the session:

```python
ctx.get_cached("roles", "Organization Administrator")  # → role UUID or None
ctx.set_cache("users", "alice@example.com", user_id)
ctx.clear_cache("groups")   # clear one type
ctx.clear_cache()           # clear all
```

Cache is automatically populated by write wrappers and `find_role_id()`.  
After SDK failures, the cache for the affected resource type should be cleared and re-populated via MCP.

## Credential Requirements

All sourced from `hosts.sh` at the repo root:

| Variable | Purpose |
|----------|---------|
| `SCC_API_KEY` | Bearer token (~7 day expiry) |
| `SCC_ORG_ID` | Organization display name |
| `SCC_API_KEY_ID` | API key UUID |
| `SCC_URL` | Base REST API URL |

Token expiry: manual rotation required via SCC UI (Settings → API Keys). Refresh endpoint is non-functional for this org.

## Related

- Agent: [.github/agents/security-cloud-control.agent.md](../../agents/security-cloud-control.agent.md)
- SCC utilities skill: [.github/skills/scc/SKILL.md](../scc/SKILL.md)
- SDK source (read-only): [scc-sdk/scc_sdk/resources/](../../../scc-sdk/scc_sdk/resources/)
