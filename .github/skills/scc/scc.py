"""
Security Cloud Control MCP Connection Tool
Connects to the SCC MCP server using stdlib only (no mcp SDK required).
Compatible with Python 3.9+. Credentials loaded from hosts.sh automatically.

Usage:
    python3 .github/skills/scc/scc.py

Note: SCC API keys expire ~7 days after generation. When expired, generate
a new key in SCC UI (Settings -> API Keys) and update hosts.sh manually.
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple


# ── Credential loading ────────────────────────────────────────────────────────

def _load_hosts_env() -> Dict[str, str]:
    """Source hosts.sh (repo root) and return SCC variables as a dict."""
    hosts_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../hosts.sh")
    )
    vars_to_extract = [
        "SCC_API_KEY", "SCC_URL", "SCC_REGIONAL_URL",
        "SCC_API_KEY_ID", "SCC_REFRESH_KEY", "SCC_ORG_ID", "SCC_USERNAME",
    ]
    print_cmds = "; ".join(f'printf "%s=%s\\n" "{v}" "${v}"' for v in vars_to_extract)
    try:
        result = subprocess.run(
            ["bash", "-c", f'. "$1" && {print_cmds}', "--", hosts_path],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(
            f"Error: Cannot source {hosts_path}\n"
            f"  Check the file exists and has no syntax errors.\n"
            f"  stderr: {exc.stderr.strip()}"
        )
    env: Dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            env[key] = value
    return env


_hosts = _load_hosts_env()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://mcp.security.cisco.com/mcp")
SCC_API_KEY = _hosts.get("SCC_API_KEY", "")
SCC_ORG_ID = _hosts.get("SCC_ORG_ID", "")

if not SCC_API_KEY:
    print("\033[91mError: SCC_API_KEY not found in hosts.sh\033[0m")
    sys.exit(1)

if not SCC_ORG_ID:
    print("\033[93mWarning: SCC_ORG_ID not set in hosts.sh.\033[0m")


# ── Raw MCP HTTP helpers ──────────────────────────────────────────────────────

def _mcp_post(method: str, params: Dict, req_id: int,
              session_id: Optional[str] = None) -> Tuple[Dict, Optional[str]]:
    """
    POST a JSON-RPC request to the MCP server and return (response_dict, session_id).
    The server responds with SSE; we parse the first `data:` line.
    """
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }).encode()

    headers = {
        "Authorization": f"Bearer {SCC_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["mcp-session-id"] = session_id

    req = urllib.request.Request(MCP_SERVER_URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            new_session_id = resp.headers.get("mcp-session-id") or session_id
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode()}") from exc

    # Parse SSE: find first non-empty data: line that looks like a JSON object
    data_line = ""
    for line in raw.splitlines():
        if line.startswith("data:"):
            candidate = line[len("data:"):].strip()
            if candidate and candidate.startswith("{"):
                data_line = candidate
                break

    if not data_line:
        raise RuntimeError(f"No data line in response: {raw[:500]}")

    return json.loads(data_line), new_session_id


def mcp_initialize() -> Tuple[Dict, Optional[str]]:
    """Send MCP initialize and return (serverInfo dict, session_id)."""
    resp, sid = _mcp_post(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "scc.py", "version": "2.0"},
        },
        req_id=1,
    )
    result = resp.get("result", {})
    return result, sid


def mcp_list_tools(session_id: Optional[str] = None) -> List[Dict]:
    """Return the list of tool dicts from tools/list."""
    resp, _ = _mcp_post("tools/list", {}, req_id=2, session_id=session_id)
    return resp.get("result", {}).get("tools", [])


def mcp_call_tool(tool_name: str, arguments: Dict,
                  session_id: Optional[str] = None, req_id: int = 3) -> Any:
    """Call a named MCP tool and return the result."""
    resp, _ = _mcp_post(
        "tools/call",
        {"name": tool_name, "arguments": arguments},
        req_id=req_id,
        session_id=session_id,
    )
    if "error" in resp:
        return {"error": resp["error"]}
    return resp.get("result", {})


# ── Display helpers ───────────────────────────────────────────────────────────

def _print_tools(tools: List[Dict]) -> None:
    for i, tool in enumerate(tools, 1):
        name = tool.get("name", "?")
        desc = tool.get("description", "")
        print(f"\033[96m{i:2d}. {name}\033[0m")
        print(f"    {desc}")
        print()


# ── Interactive REPL ──────────────────────────────────────────────────────────

def interactive_mode(tools: List[Dict], session_id: Optional[str]) -> None:
    """Simple interactive REPL for manual tool testing."""
    tool_names = {t.get("name") for t in tools}
    req_counter = [10]

    print(f"\n\033[94m{'='*70}")
    print("Interactive Tool Testing Mode")
    print("Commands:")
    print("  list               — show all available tools with schema")
    print("  call <tool> <json> — call a tool with JSON arguments")
    print("  quit               — exit")
    print(f"{'='*70}\033[0m\n")

    while True:
        try:
            user_input = input("\033[94m> \033[0m").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\033[92mGoodbye!\033[0m")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("\033[92mGoodbye!\033[0m")
            break

        if user_input.lower() == "list":
            print(f"\n\033[92m{len(tools)} tools available:\033[0m\n")
            for tool in tools:
                name = tool.get("name", "?")
                desc = tool.get("description", "")
                schema = tool.get("inputSchema", {})
                print(f"\033[93m{name}\033[0m")
                print(f"  {desc}")
                if schema.get("properties"):
                    print(f"  Args: {json.dumps(schema['properties'], indent=4)}")
                print()
            continue

        if user_input.lower().startswith("call "):
            parts = user_input[5:].split(None, 1)
            if len(parts) < 2:
                print("\033[91mUsage: call <tool_name> <json_args>\033[0m")
                print("       Example: call platform_management_list_organizations {}")
                continue

            tool_name, args_str = parts[0], parts[1]
            if tool_name not in tool_names:
                print(f"\033[91mUnknown tool: {tool_name}\033[0m")
                print(f"  Use 'list' to see available tools.")
                continue

            try:
                args = json.loads(args_str)
            except json.JSONDecodeError as exc:
                print(f"\033[91mInvalid JSON: {exc}\033[0m")
                continue

            req_counter[0] += 1
            print(f"\033[93mCalling {tool_name}...\033[0m")
            try:
                result = mcp_call_tool(tool_name, args, session_id=session_id,
                                       req_id=req_counter[0])
                print(f"\033[92mResult:\033[0m\n{json.dumps(result, indent=2)}\n")
            except Exception as exc:
                print(f"\033[91mError: {exc}\033[0m\n")
            continue

        print("\033[91mUnknown command. Type 'list', 'call <tool> <args>', or 'quit'\033[0m")


# ── Token expiry check ────────────────────────────────────────────────────────

def check_and_refresh_token() -> None:
    """
    Decode the JWT exp claim from SCC_API_KEY and exit with guidance if expired.
    No external script dependency — uses base64 (stdlib) only.
    SCC tokens encode exp in milliseconds since epoch.
    """
    import base64
    import time

    print("Checking token expiry...", end=" ", flush=True)
    try:
        parts = SCC_API_KEY.split(".")
        if len(parts) < 2:
            raise ValueError("Not a JWT")
        segment = parts[1]
        segment += "=" * ((4 - len(segment) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(segment))
        exp = payload.get("exp")
        if exp is None:
            print("\033[93mNo exp claim — proceeding\033[0m\n")
            return
        # SCC tokens store exp in milliseconds; standard JWTs use seconds.
        exp_sec = exp / 1000 if exp > 1e10 else float(exp)
        now = time.time()
        if exp_sec < now:
            print("\033[91mEXPIRED\033[0m\n")
            print("\033[91mError: SCC_API_KEY has expired.\033[0m")
            print("\033[93m  → Generate a new key: SCC UI → Settings → API Keys\033[0m")
            print("\033[93m  → Update SCC_API_KEY (and SCC_REFRESH_KEY) in hosts.sh\033[0m")
            sys.exit(1)
        remaining = exp_sec - now
        hours = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        print(f"\033[92mValid\033[0m ({hours}h {mins}m remaining)\n")
    except SystemExit:
        raise
    except Exception as exc:
        print(f"\033[93mCould not decode token ({exc}) — proceeding\033[0m\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Connect to Security Cloud Control MCP server, list available tools,
    and optionally enter interactive testing mode.

    No external dependencies — uses urllib (stdlib) to speak the MCP
    JSON-RPC-over-SSE protocol directly.
    """
    check_and_refresh_token()

    print(f"\033[94m{'='*70}")
    print("Security Cloud Control MCP — Connection Test")
    print(f"{'='*70}\033[0m")
    print(f"  MCP URL : {MCP_SERVER_URL}")
    print(f"  Org     : {SCC_ORG_ID or '<not set>'}")
    print()

    try:
        print("Initializing MCP session...", end=" ", flush=True)
        server_info, session_id = mcp_initialize()
        srv_name = server_info.get("serverInfo", {}).get("name", "unknown")
        srv_ver  = server_info.get("serverInfo", {}).get("version", "unknown")
        proto    = server_info.get("protocolVersion", "unknown")
        print(f"\033[92mOK\033[0m")
        print(f"  Server   : {srv_name} v{srv_ver}")
        print(f"  Protocol : {proto}")
        sid_display = session_id or "(stateless)"
        print(f"  Session  : {sid_display}")
        print()

        # MCP 2024-11-05 requires notifications/initialized before further calls
        try:
            _mcp_post("notifications/initialized", {}, req_id=0, session_id=session_id)
        except Exception:
            pass  # fire-and-forget; server may not respond to notifications

        print("Fetching tool list...", end=" ", flush=True)
        tools = mcp_list_tools(session_id=session_id)
        print(f"\033[92m{len(tools)} tools\033[0m\n")

        _print_tools(tools)

        print(f"\033[94m{'='*70}")
        print("✓ Connection successful!")
        print(f"{'='*70}\033[0m\n")

        print("\033[93mNote: Use the VS Code SCC agent for natural language interactions.")
        print("      This script is for connection testing and manual tool calls.\033[0m\n")

        choice = input("\033[94mEnter interactive mode for manual testing? (y/N): \033[0m").strip().lower()
        if choice in ("y", "yes"):
            interactive_mode(tools, session_id)
        else:
            print("\033[92mDone.\033[0m")

    except Exception as exc:
        print(f"\033[91m✗ Failed\033[0m")
        print(f"\033[91mError: {exc}\033[0m\n")
        print("\033[93mTroubleshooting:\033[0m")
        print("  • Verify SCC_API_KEY is valid and not expired")
        print(f"  • Check MCP_SERVER_URL: {MCP_SERVER_URL}")
        print("  • Run: bash .github/skills/scc/check_mcp.sh  (curl-based sanity check)")
        sys.exit(1)


if __name__ == "__main__":
    main()