#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCC Hybrid Context — thin wrappers over scc-sdk resources.

MCP path  : Discovery / context / read queries (via VS Code MCP tools)
SDK path  : Deterministic writes — delegates directly to scc-sdk resources

Repo constraint: scc-sdk is a read-only sub-repo. This file only calls
its public resource methods; it never modifies scc-sdk source.

Usage:
    with SCCHybridContext() as ctx:
        # Read via MCP tools in the agent, or directly:
        users = ctx.users.list(ctx.org_id)

        # Deterministic writes (after operator confirmation):
        ctx.invite_user("alice@example.com", "Alice", "Smith")
        ctx.create_group("Network Team")
"""

import os
import sys
import subprocess
from enum import Enum
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Inject scc-sdk into path without modifying the sub-repo.
# Layout: <repo>/.github/skills/scc_hybrid/ → <repo>/scc-sdk/
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_SDK_PATH = os.path.join(_REPO_ROOT, "scc-sdk")
if _SDK_PATH not in sys.path:
    sys.path.insert(0, _SDK_PATH)

from scc_sdk import (                          # noqa: E402
    Client,
    SCCError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
    ServerError,
)


# ---------------------------------------------------------------------------
# Intent routing
# ---------------------------------------------------------------------------

class OperationIntent(Enum):
    DISCOVER = "mcp"   # Read / exploration → MCP tools
    WRITE    = "sdk"   # Deterministic mutation → SDK wrappers


_WRITE_KEYWORDS    = {
    "create", "invite", "add", "assign", "update", "delete",
    "remove", "patch", "onboard", "disable", "enable", "grant", "revoke",
}
_DISCOVER_KEYWORDS = {"list", "show", "find", "search", "audit", "report", "get"}


# ---------------------------------------------------------------------------
# Hybrid context
# ---------------------------------------------------------------------------

class SCCHybridContext:
    """
    Hybrid context manager — MCP for discovery, SDK for deterministic writes.

    Startup gates (enforced in __enter__):
      1. Credentials  — SCC_API_KEY, SCC_ORG_ID, SCC_API_KEY_ID, SCC_URL present
      2. MCP          — .github/skills/scc/check_mcp.sh returns RESULT: PASS
      3. API scope    — .github/skills/scc/check_api_scopes.sh shows ✓ /organizations
      4. Org binding  — $SCC_ORG_ID display name resolved to UUID via SDK

    Session cache:  orgs · roles · users · groups  (name/email → UUID)

    Error recovery order (handle_sdk_failure):
      1. MCP re-read to detect partial success / state drift
      2. Compensate if partial success detected
      3. Operator-facing guidance with retry flag
    """

    def __init__(self, sdk_token: Optional[str] = None):
        # sdk_token override: pass a pre-refreshed access token to skip the refresh call.
        # Otherwise the refresh flow uses SCC_REFRESH_KEY + SCC_API_KEY_ID automatically.
        self._sdk_token_override = sdk_token
        self._refresh_token = os.environ.get("SCC_REFRESH_KEY", "")
        self._api_key_id    = os.environ.get("SCC_API_KEY_ID", "")
        self.org_name       = os.environ.get("SCC_ORG_ID", "")
        self.org_id: Optional[str] = os.environ.get("SCC_ORG_UUID")
        self._write_approved = self._is_true_env("SCC_WRITE_APPROVED")

        self._client: Optional[Client] = None

        self.cache: Dict[str, Dict[str, str]] = {
            "orgs": {}, "roles": {}, "users": {}, "groups": {},
        }
        self.gates_passed: Dict[str, bool] = {
            "credentials": False, "mcp": False,
            "api_scope":   False, "org_binding": False,
        }
        self.last_error: Optional[Exception] = None

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    # def _refresh_access_token(self) -> str:
    #     """Exchange SCC_REFRESH_KEY for a fresh REST API access token."""
    #     # TODO: Re-enable once SCC token refresh endpoint is restored.
    #     base_url = os.environ.get("SCC_URL", "https://api.security.cisco.com/v1/").rstrip("/")
    #     if base_url.endswith("/v1"):
    #         base_url = base_url[:-3]
    #     temp = Client(access_token=self._refresh_token, base_url=base_url, base_path="v1")
    #     try:
    #         result = temp.tokens.refresh(
    #             org_id=self.org_id or os.environ.get("SCC_ORG_UUID", ""),
    #             api_key_id=self._api_key_id,
    #             refresh_token=self._refresh_token,
    #         )
    #     finally:
    #         temp.close()
    #     access_token = result.get("access_token", "")
    #     if not access_token:
    #         raise RuntimeError("Token refresh returned no access_token.")
    #     new_refresh = result.get("refresh_token", "")
    #     if new_refresh:
    #         self._refresh_token = new_refresh
    #     return access_token

    def __enter__(self) -> "SCCHybridContext":
        self._gate_credentials()
        # Token refresh disabled (SCC side broken) — use SCC_API_KEY directly.
        sdk_token = self._sdk_token_override or os.environ.get("SCC_API_KEY", "")
        base_url = self._normalize_base_url(os.environ.get("SCC_URL", ""))
        self._client = Client(
            access_token=sdk_token,
            base_url=base_url,
            base_path="v1",
        )
        self._gate_mcp_connectivity()
        self._gate_api_scope()
        self._gate_org_binding()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            self._client.close()
        if exc_val:
            self.last_error = exc_val
        return False

    # ------------------------------------------------------------------ #
    # SDK resource pass-throughs (read operations — use directly or via MCP)
    # ------------------------------------------------------------------ #

    @property
    def organizations(self):
        """scc_sdk OrganizationsResource — list, get, create, update"""
        return self._client.organizations

    @property
    def users(self):
        """scc_sdk UsersResource — list, get, invite, disable, enable, remove, update"""
        return self._client.users

    @property
    def groups(self):
        """scc_sdk GroupsResource — list, get, create, update, delete, patch, get_users, get_assigned_roles"""
        return self._client.groups

    @property
    def roles(self):
        """scc_sdk RolesResource — list, get, patch, find_role_id"""
        return self._client.roles

    # ------------------------------------------------------------------ #
    # Thin write wrappers (operator confirmation must happen before calling)
    # ------------------------------------------------------------------ #

    def approve_writes(self) -> None:
        """Enable write operations for this context after operator confirmation."""
        self._write_approved = True

    def revoke_write_approval(self) -> None:
        """Disable write operations for this context."""
        self._write_approved = False

    def invite_user(self, email: str, first_name: str, last_name: str) -> Dict[str, Any]:
        """Invite user into $SCC_ORG_ID."""
        self._require_write_approval("invite_user")
        result = self._client.users.invite(
            org_id=self.org_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        self.set_cache("users", email, result.get("id", ""))
        return result

    def disable_user(self, email: str) -> Dict[str, Any]:
        """Disable user account."""
        self._require_write_approval("disable_user")
        return self._client.users.disable(org_id=self.org_id, email=email)

    def enable_user(self, email: str) -> Dict[str, Any]:
        """Enable user account."""
        self._require_write_approval("enable_user")
        return self._client.users.enable(org_id=self.org_id, email=email)

    def remove_user(self, email: str) -> Dict[str, Any]:
        """Remove user from org."""
        self._require_write_approval("remove_user")
        return self._client.users.remove(org_id=self.org_id, email=email)

    def update_user(self, user_id: str,
                    first_name: Optional[str] = None,
                    last_name: Optional[str] = None) -> Dict[str, Any]:
        """Update user name fields."""
        self._require_write_approval("update_user")
        return self._client.users.update(
            org_id=self.org_id, user_id=user_id,
            first_name=first_name, last_name=last_name,
        )

    def create_group(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create admin group.
        CRITICAL: appliesTo is intentionally omitted — passing it causes API failures.
        """
        self._require_write_approval("create_group")
        result = self._client.groups.create(
            org_id=self.org_id,
            name=name,
            description=description,
            # applies_to intentionally omitted
        )
        self.set_cache("groups", name, result.get("id", ""))
        return result

    def delete_group(self, group_id: str) -> bool:
        """Delete admin group by UUID."""
        self._require_write_approval("delete_group")
        return self._client.groups.delete(org_id=self.org_id, group_id=group_id)

    def add_user_to_group(self, group_id: str, user_email: str) -> Dict[str, Any]:
        """Add user to admin group."""
        self._require_write_approval("add_user_to_group")
        return self._client.groups.patch(
            org_id=self.org_id, group_id=group_id,
            users=[{"operation": "add", "id": user_email}],
        )

    def remove_user_from_group(self, group_id: str, user_email: str) -> Dict[str, Any]:
        """Remove user from admin group."""
        self._require_write_approval("remove_user_from_group")
        return self._client.groups.patch(
            org_id=self.org_id, group_id=group_id,
            users=[{"operation": "remove", "id": user_email}],
        )

    def assign_role_to_user(self, role_id: str, user_id: str) -> Dict[str, Any]:
        """Assign role to a user."""
        self._require_write_approval("assign_role_to_user")
        return self._client.roles.patch(
            org_id=self.org_id, role_id=role_id,
            users=[{"operation": "add", "id": user_id}],
        )

    def assign_role_to_group(self, role_id: str, group_id: str) -> Dict[str, Any]:
        """Assign role to an admin group."""
        self._require_write_approval("assign_role_to_group")
        return self._client.roles.patch(
            org_id=self.org_id, role_id=role_id,
            groups=[{"operation": "add", "id": group_id}],
        )

    def find_role_id(self, role_display_name: str,
                     product_name: str = "Security Cloud Control") -> Optional[str]:
        """Resolve role display name → UUID, with cache."""
        cached = self.get_cached("roles", role_display_name)
        if cached:
            return cached
        role_id = self._client.roles.find_role_id(
            org_id=self.org_id,
            product_name=product_name,
            role_display_name=role_display_name,
        )
        if role_id:
            self.set_cache("roles", role_display_name, role_id)
        return role_id

    # ------------------------------------------------------------------ #
    # Intent classification
    # ------------------------------------------------------------------ #

    def classify_intent(self, user_input: str) -> OperationIntent:
        """
        Classify natural-language input as DISCOVER (→MCP) or WRITE (→SDK).

        Examples:
            "list all users"           → DISCOVER
            "invite alice@example.com" → WRITE
            "assign admin role"        → WRITE
            "show groups"              → DISCOVER
        """
        lower = user_input.lower()
        if any(kw in lower for kw in _WRITE_KEYWORDS):
            return OperationIntent.WRITE
        return OperationIntent.DISCOVER

    def route_operation(self, intent: OperationIntent) -> str:
        """Return "mcp" or "sdk"."""
        return intent.value

    # ------------------------------------------------------------------ #
    # Session cache
    # ------------------------------------------------------------------ #

    def get_cached(self, cache_type: str, key: str) -> Optional[str]:
        return self.cache.get(cache_type, {}).get(key)

    def set_cache(self, cache_type: str, key: str, value: str) -> None:
        self.cache.setdefault(cache_type, {})[key] = value

    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        if cache_type:
            self.cache.get(cache_type, {}).clear()
        else:
            for v in self.cache.values():
                v.clear()

    # ------------------------------------------------------------------ #
    # Error recovery
    # ------------------------------------------------------------------ #

    def handle_sdk_failure(self, error: Exception, operation: str,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Recovery precedence:
          1. MCP verify  — re-read state to detect partial success / drift
          2. Compensate  — corrective action if partial success detected
          3. Operator    — actionable guidance with retry flag
        """
        self.last_error = error
        recovery = {
            "error":             str(error),
            "operation":         operation,
            "step_1_verify":     self._mcp_verify(operation, context or {}),
            "step_2_compensate": None,
            "step_3_action":     self._operator_guidance(error, operation),
        }
        if recovery["step_1_verify"].get("partial_success"):
            recovery["step_2_compensate"] = {
                "message": f"Partial success detected for '{operation}' — review and compensate."
            }
        return recovery

    def _mcp_verify(self, operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Re-read state via MCP. Phase 2 will wire live MCP tool calls here."""
        return {
            "operation":       operation,
            "partial_success": False,
            "actual_state":    None,
            "message":         f"[MCP verify] Re-read pending for '{operation}'",
        }

    def _operator_guidance(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Map SDK exception type to operator-facing remediation."""
        if isinstance(error, AuthenticationError):
            return {"retry": False, "guidance": (
                "Token expired or invalid. Rotate SCC_API_KEY in hosts.sh "
                "(SCC UI → Settings → API Keys)."
            )}
        if isinstance(error, ForbiddenError):
            return {"retry": False, "guidance": (
                f"Insufficient privileges for '{operation}'. "
                "Verify the API key has the Organization Administrator role."
            )}
        if isinstance(error, NotFoundError):
            return {"retry": False, "guidance": (
                f"Resource not found for '{operation}'. "
                "Verify org/user/group/role identifiers."
            )}
        if isinstance(error, ValidationError):
            return {"retry": True, "guidance": (
                f"Validation error for '{operation}': {error}. "
                "Review the request parameters."
            )}
        if isinstance(error, ServerError):
            return {"retry": True, "guidance": "SCC API 5xx error — transient. Wait and retry."}
        return {"retry": True, "guidance": f"Unexpected error: {error}"}

    # ------------------------------------------------------------------ #
    # Startup gates
    # ------------------------------------------------------------------ #

    def _gate_credentials(self) -> None:
        # SCC_REFRESH_KEY excluded — token refresh disabled until SCC side is restored.
        required = ["SCC_API_KEY", "SCC_ORG_ID", "SCC_API_KEY_ID", "SCC_ORG_UUID", "SCC_URL"]
        missing  = [v for v in required if not os.environ.get(v)]
        if missing:
            raise RuntimeError(
                f"Missing environment variables: {', '.join(missing)}\n"
                "Remediation: export vars with 'set -a; source hosts.sh; set +a'. "
                "If imports fail first, install dependencies with "
                "'python3 -m pip install -r scc-sdk/requirements.txt'."
            )
        if not self.org_id:
            self.org_id = os.environ.get("SCC_ORG_UUID", "")
        self.gates_passed["credentials"] = True

    def _gate_mcp_connectivity(self) -> None:
        script = os.path.join(_REPO_ROOT, ".github", "skills", "scc", "check_mcp.sh")
        r = subprocess.run(
            ["bash", script], capture_output=True, text=True, timeout=30, cwd=_REPO_ROOT
        )
        if r.returncode != 0 or "RESULT: PASS" not in r.stdout:
            raise RuntimeError(
                "MCP gate failed. "
                "Remediation: run .github/skills/scc/check_mcp.sh for diagnostics."
            )
        self.gates_passed["mcp"] = True

    def _gate_api_scope(self) -> None:
        script = os.path.join(_REPO_ROOT, ".github", "skills", "scc", "check_api_scopes.sh")
        r = subprocess.run(
            ["bash", script], capture_output=True, text=True, timeout=30, cwd=_REPO_ROOT
        )
        has_org_read_access = "REST API read access: ✓ YES" in r.stdout
        if r.returncode != 0 or not has_org_read_access:
            msg = "API token expired." if "EXPIRED" in r.stdout else "Required API scope check failed."
            raise RuntimeError(
                f"API scope gate failed: {msg} "
                "Remediation: run .github/skills/scc/check_api_scopes.sh and rotate SCC_API_KEY in hosts.sh if needed."
            )
        self.gates_passed["api_scope"] = True

    def _require_write_approval(self, operation: str) -> None:
        if not self._write_approved:
            raise RuntimeError(
                f"Write operation blocked: {operation}. "
                "Call approve_writes() after explicit operator confirmation, "
                "or set SCC_WRITE_APPROVED=true for approved automation."
            )

    @staticmethod
    def _is_true_env(name: str) -> bool:
        return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _normalize_base_url(raw_url: str) -> str:
        parsed = urlparse(raw_url.strip())
        if parsed.scheme != "https" or not parsed.netloc:
            raise RuntimeError(
                "Invalid SCC_URL. Expected an https URL, for example https://api.security.cisco.com/v1/."
            )
        return f"{parsed.scheme}://{parsed.netloc}"

    def _gate_org_binding(self) -> None:
        """Resolve org display name → UUID using SDK directly (no shell script)."""
        try:
            result = self._client.organizations.list(name=self.org_name)
            orgs   = result.get("organizations", [])
            match  = next((o for o in orgs if o.get("name") == self.org_name), None)
            if not match:
                available = [o.get("name") for o in orgs]
                raise RuntimeError(
                    f"Org '{self.org_name}' not found. Available: {available}\n"
                    "Remediation: Verify SCC_ORG_ID in hosts.sh"
                )
            self.org_id = match["id"]
            self.set_cache("orgs", self.org_name, self.org_id)
            self.gates_passed["org_binding"] = True
        except SCCError as e:
            raise RuntimeError(f"Org binding SDK error: {e}")

    # ------------------------------------------------------------------ #
    # Status
    # ------------------------------------------------------------------ #

    def is_ready(self) -> bool:
        return all(self.gates_passed.values())

    def get_status(self) -> Dict[str, Any]:
        return {
            "org_name":    self.org_name,
            "org_id":      self.org_id,
            "gates":       self.gates_passed,
            "cache_stats": {k: len(v) for k, v in self.cache.items()},
            "last_error":  str(self.last_error) if self.last_error else None,
        }


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("SCC Hybrid Context — smoke test")
    print("=" * 50)
    with SCCHybridContext() as ctx:
        print(f"✓ Org   : {ctx.org_name}")
        print(f"✓ UUID  : {ctx.org_id}")
        print(f"✓ Gates : {ctx.gates_passed}")

        samples = [
            ("list all users",          OperationIntent.DISCOVER),
            ("invite alice@example.com", OperationIntent.WRITE),
            ("create security group",   OperationIntent.WRITE),
            ("show all roles",          OperationIntent.DISCOVER),
        ]
        print("\nIntent routing:")
        for text, expected in samples:
            got  = ctx.classify_intent(text)
            mark = "✓" if got == expected else "✗"
            print(f"  {mark}  '{text}'  →  {got.name} ({got.value})")

        print("\n✓ Ready.")
