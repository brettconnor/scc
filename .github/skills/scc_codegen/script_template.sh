#!/usr/bin/env bash
# SCC Hybrid Script Template
# 
# Usage: Copy this file and customize the Python section for your workflow.
# 
# DO NOT modify this template directly. Instead:
#   1. cp script_template.sh my_workflow.sh
#   2. Edit the PYTHON CODE SECTION (marked below)
#   3. Run: bash my_workflow.sh
# 
# Why this template exists:
#   - Ensures hosts.sh vars are properly exported to Python
#   - Prevents "Missing environment variables" errors
#   - Standardizes credential handling across all scripts
#
# Key pattern: set -a; source hosts.sh; set +a && python3 << 'EOF'
#   ↓
#   Exports all vars from hosts.sh to this shell
#   ↓
#   && chains to Python execution (preserves exported vars)
#   ↓
#   Child Python process inherits exported environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

cd "${REPO_ROOT}"

# ============================================================================
# PREFLIGHT CHECKS
# ============================================================================

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH"
  exit 1
fi

if [[ ! -f "hosts.sh" ]]; then
  echo "ERROR: hosts.sh not found at repo root"
  echo "Remediation: cp hosts.sh.example hosts.sh && edit with real values"
  exit 1
fi

# Ensure dependencies are available
if ! python3 -c 'import requests' >/dev/null 2>&1; then
  echo "Installing scc-sdk dependencies..."
  python3 -m pip install -r "scc-sdk/requirements.txt" || \
    PIP_INDEX_URL=https://pypi.org/simple python3 -m pip install -r "scc-sdk/requirements.txt"
fi

# ============================================================================
# EXECUTE PYTHON WORKFLOW
# ============================================================================
# 
# CRITICAL: set -a; source hosts.sh; set +a BEFORE python3
#
# Do NOT do this:
#   python3 << 'EOF'
#   os.system("source hosts.sh")  # ❌ Won't work — subshell
#   ...
#
# DO this:
#   set -a; source hosts.sh; set +a && python3 << 'EOF'
#   # vars now available to Python process
#   ...
# ============================================================================

set -a
source "hosts.sh"
set +a

python3 << 'PYTHON_EOF'

import sys
import os

# Add hybrid skill to path
sys.path.insert(0, ".github/skills/scc_hybrid")

from scc_hybrid_context import SCCHybridContext

# ============================================================================
# CUSTOMIZE THIS SECTION FOR YOUR WORKFLOW
# ============================================================================

print("\n" + "=" * 80)
print("SCC Hybrid Workflow")
print("=" * 80 + "\n")

with SCCHybridContext() as ctx:
    print(f"✓ Connected to org: {ctx.org_id}\n")
    
    # EXAMPLE: List active users
    users_response = ctx.users.list(ctx.org_id)
    users = users_response.get('users', [])
    active_users = [u for u in users if u.get('status') == 'ACTIVE']
    
    print(f"Active users: {len(active_users)} / {len(users)}\n")
    
    for user in active_users:
        print(f"  {user['email']:<35} {user['fullName']:<25}")
    
    # ADD YOUR WORKFLOW LOGIC BELOW THIS LINE
    # Examples:
    #   - ctx.users.list(ctx.org_id)
    #   - ctx.groups.list(ctx.org_id)
    #   - ctx.invite_user("email@example.com", "First", "Last")
    #   - ctx.create_group("Group Name")
    #   - ctx.assign_role_to_user(role_id, user_id)
    # See SKILL.md for full API reference

print("\n" + "=" * 80)
print("Done")
print("=" * 80 + "\n")

PYTHON_EOF

exit_code=$?
if [[ $exit_code -ne 0 ]]; then
  echo "Workflow failed with exit code $exit_code"
  exit $exit_code
fi
