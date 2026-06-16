---
name: learn_fm_api
description: Comprehensive reference documentation for Security Cloud Control Firewall Management Center API. Includes getting started guides, authentication patterns, search syntax, regional endpoints, RESTful operations, cdFMC API usage examples, and Python SDK information. Use when learning FMC API fundamentals, understanding authentication, exploring API resources, or implementing firewall operations.
---

# Security Cloud Control Firewall Management Center API Reference

This skill provides comprehensive documentation and reference materials for working with the Cisco Security Cloud Control Firewall Management Center API.

## When to Use This Skill

Use this skill when you need to:
- Understand FMC API fundamentals and getting started
- Learn about authentication methods and token management
- Explore API endpoints and resources
- Understand regional deployment and base URLs
- Learn search syntax and query patterns
- Work with cdFMC-specific operations
- Access Python SDK documentation
- Reference API specifications (OpenAPI/YAML)

## Documentation Structure

### Core Guides

1. **[getting_started.md](getting_started.md)** - Start here for API fundamentals
   - Supported RESTful operations (GET, POST, PATCH, PUT, DELETE)
   - API resources overview (Inventory, Connectors, cdFMC, Objects, Users, etc.)
   - API user prerequisites and permissions
   - Regional base URLs for all regions
   - Quick start examples with curl
   - Common operations walkthrough

2. **[api_authc.md](api_authc.md)** - Authentication and token management
   - Creating API tokens
   - JWT token structure and claims
   - User roles and privileges
   - Token expiry and refresh patterns

3. **[searching.md](searching.md)** - Search and query syntax
   - Lucene query syntax for list endpoints
   - Field-based searching
   - Wildcard searches
   - Time range queries
   - URL encoding guidelines

### Development Resources

4. **[dev/sdk.md](dev/sdk.md)** - Python SDK
   - Installation instructions
   - SDK documentation links
   - PyPI package information

### API Specifications

5. **[ref/scc_fm_api/overview.md](ref/scc_fm_api/overview.md)** - Security Cloud Control Firewall Manager API
   - OpenAPI specification (YAML)
   - Comprehensive endpoint documentation

6. **[ref/cdfmc-api/overview.md](ref/cdfmc-api/overview.md)** - Cloud-delivered FMC API
   - cdFMC-specific endpoints
   - OpenAPI specification (YAML)

## Key Concepts

### Regional Deployments

The API is available in multiple regions:
- **US**: `https://api.us.security.cisco.com/firewall`
- **EU**: `https://api.eu.security.cisco.com/firewall`
- **APJ**: `https://api.apj.security.cisco.com/firewall`
- **Australia**: `https://api.au.security.cisco.com/firewall`
- **India**: `https://api.in.security.cisco.com/firewall`
- **UAE**: `https://api.uae.security.cisco.com/firewall`
- **FedRAMP**: `https://manage.secure.cisco/api/rest`

### API Resource Categories

1. **Inventory Management** (`/v1/inventory/`) - Devices, managers, templates
2. **Connector Management** (`/v1/connectors/`) - Communication connectors
3. **Cloud-delivered FMC** (`/v1/cdfmc/`) - cdFMC operations
4. **Object Management** (`/v1/objects/`) - Network objects, services, zones
5. **Policy Management** - Access policies, NAT, security rules
6. **Remote Access VPN** (`/v1/ravpn/`) - VPN sessions and MFA
7. **Search** (`/v1/search`) - Cross-resource searches
8. **Changelogs** (`/v1/changelogs`) - Change history
9. **Transactions** (`/v1/transactions`) - Async operation tracking

### Authentication Pattern

All API requests require Bearer token authentication:

```http
Authorization: Bearer $SCC_FMC_API_KEY
```

Where `$SCC_FMC_API_KEY` is obtained from the Security Cloud Control UI (Firewall Management Center API token).

### Common Operations

#### List Devices
```bash
curl -X GET \
  --url https://api.us.security.cisco.com/firewall/v1/inventory/devices \
  --header "Authorization: Bearer $SCC_FMC_API_KEY"
```

#### Get cdFMC Information
```bash
curl -X GET \
  --url https://api.us.security.cisco.com/firewall/v1/inventory/managers?q=deviceType:CDFMC \
  --header "Authorization: Bearer $SCC_FMC_API_KEY"
```

#### Search with Query
```bash
curl -X GET \
  --url "https://api.us.security.cisco.com/firewall/v1/inventory/devices?q=name:*firewall*" \
  --header "Authorization: Bearer $SCC_FMC_API_KEY"
```

## Usage Guidelines

### For Discovery and Learning

When a user asks about:
- "How do I authenticate to the FMC API?"
- "What are the available endpoints?"
- "How do I search for devices?"
- "What regions are supported?"

→ Reference the appropriate documentation file and provide specific examples.

### For Implementation

When implementing API operations:
1. Start with `getting_started.md` for context
2. Check `api_authc.md` for authentication details
3. Use `searching.md` for query syntax
4. Reference OpenAPI specs for detailed endpoint information

### Integration with FMC Agent

The FMC agent should use this skill to:
- Look up API endpoint details
- Verify authentication patterns
- Understand regional deployments
- Reference search syntax
- Access example curl commands
- Guide users through API operations

## Best Practices

1. **Always use environment variables** for API tokens (never hardcode)
2. **Check regional endpoint** before making requests
3. **Use pagination** for list operations (default limit: 50)
4. **Track async operations** via transaction API
5. **URL-encode query parameters** for search operations
6. **Handle errors gracefully** with proper HTTP status code checks

## Quick Reference

| Need | Document | Section |
|------|----------|---------|
| First API call | getting_started.md | Quick Start Examples |
| Create API token | api_authc.md | Creating an API Token |
| User roles | api_authc.md | Token Claims |
| Search syntax | searching.md | How to Search |
| Regional URLs | getting_started.md | Base URL |
| Python SDK | dev/sdk.md | Installation |
| cdFMC operations | getting_started.md | Example 4-7 |
| API spec | ref/scc_fm_api/overview.md | OpenAPI YAML |

## Next Steps After Reading

After consulting this skill documentation:
1. Set up authentication (API token from UI)
2. Choose appropriate regional endpoint
3. Test with a simple GET request
4. Implement required operations
5. Handle errors and pagination
6. Track async operations if needed
