#!/usr/bin/env python3
"""
test_sdk.py - Test SCC Platform SDK installation and connectivity

Usage:
    python3 .github/skills/scc/test_sdk.py

Validates:
- SDK is installed at /home/wolfy/scc/scc-sdk/
- SDK imports work correctly
- API client can be configured
- Test API call succeeds (list organizations)
"""

import sys
import os

# Add SDK to path
SDK_PATH = '/home/wolfy/scc/scc-sdk'
sys.path.insert(0, SDK_PATH)

def check_sdk_installation():
    """Verify SDK is installed"""
    print("=" * 60)
    print("SCC Platform SDK Test")
    print("=" * 60)
    print()
    
    print(f"Checking SDK installation at: {SDK_PATH}")
    
    if not os.path.exists(SDK_PATH):
        print(f"✗ SDK directory not found: {SDK_PATH}")
        print()
        print("The SDK should be available in the scc-sdk/ directory.")
        print("Check if it's a git submodule or needs to be cloned.")
        return False
    
    print("✓ SDK directory exists")
    
    # Check for main SDK package
    sdk_package = os.path.join(SDK_PATH, 'scc_sdk')
    if not os.path.exists(sdk_package):
        print(f"✗ SDK package not found: {sdk_package}")
        return False
    
    print("✓ SDK package found")
    print()
    
    return True

def test_sdk_imports():
    """Test SDK imports"""
    print("Testing SDK imports...")
    
    try:
        from scc_sdk import Client
        print("✓ Client imported from scc_sdk")
    except ImportError as e:
        print(f"✗ Failed to import Client: {e}")
        return False
    
    try:
        from scc_sdk import SCCError, AuthenticationError
        print("✓ Exception classes imported")
    except ImportError as e:
        print(f"✗ Failed to import exceptions: {e}")
        return False
    
    print()
    return True

def test_api_connectivity():
    """Test API connectivity with SDK"""
    print("Testing API connectivity...")
    
    # Get credentials from environment
    api_key = os.getenv('SCC_API_KEY')
    base_url = os.getenv('SCC_REGIONAL_URL') or os.getenv('SCC_URL')
    
    if not api_key:
        print("✗ SCC_API_KEY not set")
        print("  Load environment: set -a; source hosts.sh; set +a")
        return False
    
    if not base_url:
        print("✗ SCC_REGIONAL_URL or SCC_URL not set")
        print("  Load environment: set -a; source hosts.sh; set +a")
        return False
    
    # Strip /v1/ suffix if present (SDK will add it)
    base_url = base_url.rstrip('/')
    if base_url.endswith('/v1'):
        base_url = base_url[:-3]
    
    print(f"✓ Credentials loaded")
    print(f"  Endpoint: {base_url}")
    print(f"  Token: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    try:
        from scc_sdk import Client
        
        # Initialize client
        client = Client(access_token=api_key, base_url=base_url.rstrip('/'))
        print("✓ SDK client initialized")
        print()
        
        # Make test API call - list organizations
        print("Making test API call (list organizations)...")
        
        try:
            organizations = client.organizations.list()
            print("✓ API call succeeded")
            
            # Handle list() which may return a list or None
            if organizations and isinstance(organizations, list):
                print(f"  Organizations found: {len(organizations)}")
                
                if len(organizations) > 0:
                    org = organizations[0]
                    # Handle both dict and object responses
                    if isinstance(org, dict):
                        org_name = org.get('name', 'N/A')
                    else:
                        org_name = getattr(org, 'name', 'N/A')
                    print(f"  Sample org: {org_name}")
            else:
                print(f"  Organizations found: 0 or None")
            
            print()
            return True
            
        except Exception as e:
            print(f"✗ API call failed: {e}")
            print()
            print("This might be due to:")
            print("  - Token doesn't have organization read permissions")
            print("  - API endpoint requires different authentication")
            print("  - Token has expired")
            print()
            return False
        
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False

def main():
    """Main test flow"""
    
    # Test 1: SDK installation
    if not check_sdk_installation():
        sys.exit(1)
    
    # Test 2: SDK imports
    if not test_sdk_imports():
        sys.exit(1)
    
    # Test 3: API connectivity
    if not test_api_connectivity():
        print("=" * 60)
        print("⚠  SDK is installed but API connectivity test failed")
        print("=" * 60)
        print()
        print("SDK installation is correct, but API access may need")
        print("additional configuration or permissions.")
        print()
        print("Next steps:")
        print("  - Verify token has org read permissions")
        print("  - Check SCC_API_KEY is not expired")
        print("  - Use @SCC agent for interactive operations")
        print("  - See: bash .github/skills/scc/check_api_scopes.sh")
        sys.exit(1)
    
    # All tests passed
    print("=" * 60)
    print("✓ All tests passed")
    print("=" * 60)
    print()
    print("SDK is properly installed and configured.")
    print()
    print("Next steps:")
    print("  - Use @SCC agent for user management operations")
    print("  - Check connectivity: bash .github/skills/scc/check_mcp.sh")
    print("  - List orgs: bash .github/skills/scc/get_scc_org.sh")
    print("  - Check token: bash .github/skills/scc/check_api_scopes.sh")

if __name__ == '__main__':
    main()
