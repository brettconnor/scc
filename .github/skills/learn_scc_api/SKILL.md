---
name: learn_scc_api
description: Comprehensive reference documentation for Security Cloud Control Platform Management API. Includes getting started guides, authentication patterns, pagination, regional endpoints, RESTful operations, user and organization management, common objects, and Python SDK information. Use when learning SCC API fundamentals, understanding authentication, exploring API resources, or implementing platform administration operations.
---

# Security Cloud Control Platform Management API Reference

This skill provides comprehensive documentation and reference materials for working with the Cisco Security Cloud Control Platform Management API.

## When to Use This Skill

Use this skill when you need to:
- Understand SCC API fundamentals and getting started
- Learn about authentication methods and token management
- Explore API endpoints and resources
- Understand regional deployment and base URLs
- Learn pagination patterns
- Work with platform management operations (users, groups, organizations, roles)
- Work with common objects (networks, network groups)
- Access Python SDK documentation
- Reference API specifications (OpenAPI/YAML)
- Troubleshoot API issues

## Documentation Structure

### Core Guides

1. **[intro.md](intro.md)** - API introduction and overview
   - Security Cloud Control platform overview
   - API capabilities and use cases
   - Integrated products (AI Defense, FMC, Multicloud Defense, Secure Access, Secure Workload)
   - HTTP methods and response codes

2. **[getting_started.md](getting_started.md)** - Start here for API fundamentals
   - REST interface and OpenAPI specification
   - Platform Management capabilities (Organizations, Subscriptions, Users, Roles, etc.)
   - Common Objects capabilities (Networks, Network Groups)
   - User requirements and prerequisites
   - Base URLs (Global and Regional)
   - Regional endpoints for all regions

3. **[authc.md](authc.md)** - Authentication and token management
   - Creating API keys from Security Cloud Control UI
   - Bearer token authentication
   - Role-based access control
   - Token expiry and refresh patterns
   - Security best practices for credentials

### Additional Guides

4. **[guides/pagination.md](guides/pagination.md)** - Pagination patterns
   - Cursor-based pagination
   - Max records per request
   - Collection operations

5. **[guides/tshoot.md](guides/tshoot.md)** - Troubleshooting guide
   - Common issues and resolutions
   - Error handling patterns

### Development Resources

6. **[dev/sdk.md](dev/sdk.md)** - Python SDK
   - Installation instructions
   - SDK features and capabilities
   - GitHub repository link (cisco-scc-python-sdk)
   - Local SDK path (~/scc/scc-sdk)

### API Specifications

7. **[ref/platform/overview.md](ref/platform/overview.md)** - Platform Management API
   - OpenAPI specification (YAML)
   - Organizations, Users, Admin Groups, Roles, Subscriptions endpoints
   - Comprehensive endpoint documentation

8. **[ref/objects/overview.md](ref/objects/overview.md)** - Common Objects API
   - OpenAPI specification (YAML)
   - Network objects and network groups endpoints

## Key Concepts

### Regional Deployments

The API is available in multiple regions:
- **Global**: `https://api.security.cisco.com/v1/`
- **US**: `https://api.us.security.cisco.com`
- **EU**: `https://api.eu.security.cisco.com`
- **APJ**: `https://api.apj.security.cisco.com`
- **Australia**: `https://api.au.security.cisco.com`
- **India**: `https://api.in.security.cisco.com`
- **UAE**: `https://api.uae.security.cisco.com`

### API Resource Categories

#### Platform Management
1. **Organizations** - Create, view, and update organizations (managed and standalone)
2. **Subscriptions** - Software subscription lifecycle management
3. **Users** - User lifecycle operations (list, view, suspend, enable, invite, reset)
4. **User Groups** - Admin group membership queries
5. **Admin Groups** - Group management and organization access
6. **Roles** - Role assignment and management
7. **Refresh Token** - Token renewal operations

#### Common Objects
1. **Objects** - View network objects or groups
2. **Networks** - Network object CRUD operations
3. **Network Groups** - Network group CRUD operations

### Authentication Pattern

All API requests require Bearer token authentication:

```http
Authorization: Bearer $SCC_API_KEY
```

Where `$SCC_API_KEY` is obtained from the Security Cloud Control UI (Platform Management → API Keys).

### User Requirements

To make API requests, users must:
- Have an account with API access (Organization Member or Organization Administrator role)
- Have a valid access token
- Be assigned appropriate roles for the desired operations

### Role-Based Access Control

- **Organization Member**: Can access read-only APIs
- **Organization Administrator**: Can create and modify organizations and users
- **Custom Roles**: May have varying API access levels
- Only platform and product administrators can create API keys
- API keys inherit permissions from assigned roles

### Common Operations

#### User Management
- List all users in an organization
- View user details
- Invite new users
- Suspend or enable users
- Resend email invitations
- Reset passwords and MFA
- Modify user information

#### Group Management
- List all admin groups
- View admin group details
- Add or remove users from groups
- Manage organization access for groups
- Modify group properties
- Delete admin groups

#### Organization Management
- Create managed or standalone organizations
- View organization details
- Update organization settings
- Validate claim codes

#### Role Management
- List available roles
- View role details
- Assign roles to users
- Remove role assignments

#### Common Objects
- Create, view, update, and delete network objects
- Create, view, update, and delete network groups

### Pagination

Collection operations support pagination:
- Default page size: 100 records
- Use `cursor` parameter to navigate pages (default: 1)
- Use `max` parameter to control page size

### Python SDK

The `cisco-scc-python-sdk` provides:
- Full API operation support via OpenAPI specification
- Automatic error handling and logging
- Built-in retry logic
- Simplified pagination control
- Python 3.7+ support

Install via pip:
```bash
pip install cisco-scc-python-sdk
```

Local SDK path: `~/scc/scc-sdk`

## Integration with Agent Operations

When the SCC agent needs to:
- **Understand API structure**: Reference getting_started.md for endpoints and capabilities
- **Implement authentication**: Reference authc.md for token patterns
- **Handle pagination**: Reference guides/pagination.md for cursor-based navigation
- **Troubleshoot issues**: Reference guides/tshoot.md for common problems
- **Use SDK**: Reference dev/sdk.md for Python library usage
- **Reference OpenAPI specs**: Use ref/platform/ and ref/objects/ specifications

## Best Practices

1. **Security**: Never share API keys, tokens, or credentials
2. **Token Management**: Monitor token expiry and refresh proactively
3. **Pagination**: Use appropriate page sizes for collection operations
4. **Error Handling**: Implement retry logic for transient failures
5. **Regional Routing**: Use appropriate regional endpoint for your organization
6. **Role Management**: Assign minimal required roles following least privilege principle
7. **SDK Usage**: Prefer SDK over raw HTTP for automatic error handling and retries
