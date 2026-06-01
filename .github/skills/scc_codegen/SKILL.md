---
name: scc_codegen
description: Detects SCC workflow requests that should be implemented as one-shot SDK scripts and provides CodeGuard security review guidance before code handoff.
---

# SCC Workflow Script Planning and Secure Codegen Skill

Use this skill when SCC operators ask for repeatable workflows, especially bulk onboarding/offboarding across users, groups, roles, or multiple organizations.

## When to Use

Activate this skill when one or more are present:
- Multi-step operations with repeated patterns
- Bulk onboarding or offboarding
- Multiple organizations in one request
- Operator asks for reusable automation or a workflow
- Requirement for dry-run, idempotency, rollback, or audit reports

## Files

| File | Purpose |
|------|---------|
| `script_template.sh` | Canonical reusable SCC workflow template with preflight checks, dependency install, and exported `hosts.sh` environment pattern |

## Reusable Workflow Template

Use this skill-owned template when creating repeatable SCC workflows:

```bash
cp .github/skills/scc_codegen/script_template.sh scc_admin_workflow.sh
# Then edit the PYTHON CODE SECTION in scc_admin_workflow.sh
bash scc_admin_workflow.sh
```

The template automatically:
- ✓ Checks for Python and `hosts.sh`
- ✓ Installs `scc-sdk` dependencies
- ✓ Exports environment variables correctly (`set -a; source hosts.sh; set +a`)
- ✓ Provides starter code with documented API examples

## Required Behavior

1. Detect workflow intent and classify as a Script Candidate Workflow.
2. Propose a one-shot script plan before making mutation calls.
3. Ask for approval on the plan before generating code.
4. If approved, generate deterministic SDK-style code with clear stages.
5. Include CodeGuard review guidance notes with final code handoff.

## Script Plan Template

Every plan should include:
1. Scope and impact count
2. Input contract (CSV/JSON schema and validation)
3. Preflight gates (credentials, MCP, API scope, org binding)
4. Dry-run behavior (no writes)
5. Execution stages (deterministic write order)
6. Verification checks (post-write reads)
7. Rollback or compensation path
8. Audit artifact format (success/failure with IDs and timestamps)

## Security Review Guidance

Before returning new or modified code, consider:

1. Baseline skill:
- `codeguard/skills/software-security/SKILL.md`

2. Always-on rules:
- `codeguard-1-hardcoded-credentials.md`
- `codeguard-1-crypto-algorithms.md`
- `codeguard-1-digital-certificates.md`

3. Language-specific rules:
- Apply rules listed in `codeguard/skills/software-security/SKILL.md` for each language in generated artifacts.

4. Output requirement:
- Include a Security Review Note with:
  - Security checks considered
  - Findings and mitigations
  - Residual risk notes

If security review is skipped or deferred, include a brief note explaining why and suggest next steps.

## SCC-Specific Guardrails

- Default to MCP for discovery, SDK path for deterministic writes.
- Keep `appliesTo` out of group creation payloads.
- Preserve explicit confirmation gates for write operations.
- Prefer dry-run first for any bulk or cross-org workflow.
