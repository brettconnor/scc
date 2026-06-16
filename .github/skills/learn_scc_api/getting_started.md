# Getting Started

The Security Cloud Control API implements a REST interface that is described by version 3.x of the OpenAPI specification. The API operations use JSON for all requests and responses.

To access the Security Cloud Control API, you must first get an access token from the user interface. With this access token, you can use any REST client to make requests to the API.

## API Capabilities

The Security Cloud Control API provides the following capabilities:

### Platform Management

The Security Cloud Control API provides the following capabilities for platform management:

- **Organizations** - Create, view, and update organizations provisioned on Security Cloud Control.
- **Subscriptions** - Create, view, update, activate, and deactivate software subscriptions on a Security Cloud Control organization.
- **ClaimInfo** - Validate a claim code and retrieve details about the claim code for a specific organization.
- **Users** - List all users, view user details, suspend and enable users, resend email invites, reset passwords, reset multi-factor authentication, and modify user information.
- **User Groups** - List all admin groups that include the user.
- **Admin Groups** - List all admin groups within an organization. List which organizations can access an admin group, view details for an admin group, add or remove users and managed organizations from an admin group. Modify admin group details, and delete admin groups.
- **Roles** - List roles, view details for a role, and assign or remove roles from users.
- **Refresh Token** - Get a new access and refresh token.

### Common Objects

The Security Cloud Control API provides the following capabilities for common object services:

- **Objects** - View network objects or groups.
- **Networks** - Create, update, or delete network objects.
- **Network Groups** - Create, update, or delete network groups.

## User Requirements

To make an API request, you must:

- Have an account with API access. The default Organization Member and Organization Administrator roles have API access, but custom user roles may not.
- Have an access token. You can get an access token by following the steps in How to Get an API Key.

## Base URL

### Global URL

Global API requests begins with the following Base URL:

```
https://api.security.cisco.com/v1/
```

### Regional URLs

Some API requests are regional. Regional requestions use the following base URLs depending on region:

- **US**: `https://api.us.security.cisco.com`
- **EU**: `https://api.eu.security.cisco.com`
- **APJ**: `https://api.apj.security.cisco.com`
- **Australia**: `https://api.au.security.cisco.com`
- **India**: `https://api.in.security.cisco.com`
- **UAE**: `https://api.uae.security.cisco.com`

## Quick Start Examples

### 1. Authorization

Every API request must include an access token in the header. To get an access token, follow the steps in How to Create an API Key.

### 2. List Organizations

Organization IDs are unique identifiers (UUIDs) that Security Cloud Control assigns to each organization. Use the List Organizations operation to list all of the organizations you have access to in Security Cloud Control.

To get a list of organizations and their IDs, make the following request:

**Request**

```bash
curl --location 'https://api.security.cisco.com/v1/organizations' \
--header 'Authorization: Bearer <token>'
```

**Response**

```json
{
  "organizations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "Acme Corp",
      "type": "STANDALONE"
    }
  ]
}
```

### 3. Get Organization Details

From the list of organizations in the response, select one organizations.id to retrieve more details about that organization. Then, use the Get Organization Details operation with the organizations.id in the previous example as the {orgId} parameter in this example.

**Request**

```bash
curl -L --request GET \
--url https://api.security.cisco.com/v1/organizations/550e8400-e29b-41d4-a716-446655440003 \
--header 'Authorization: Bearer <token>'
```

**Response**

```json
{
  "id": "550e8400-e29b-41d4-a716-4466554400003",
  "name": "Acme Corporation",
  "regionCode": "NAM",
  "regionDescription": "North America",
  "created": "2025-10-10T10:15:30Z",
  "type": "MANAGED",
  "managedOrgIds": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "managerOrgIds": [
    "550e8400-e29b-41d4-a716-446655440003",
    "550e8400-e29b-41d4-a716-446655440004"
  ]
}
```

### 4. Create an Admin Group

Using the same organization ID, create an admin group with name, description, and what the group applies to using the Create Admin Group operation.

**Request**

```bash
curl -L --request POST \
--url https://api.security.cisco.com/v1/organizations/550e8400-e29b-41d4-a716-446655440003/adminGroups \
--header 'Content-Type: application/json' \
--header 'Accept: application/json' \
--header 'Authorization: Bearer <token>' \
--data '{
  "name": "Engineering_Team",
  "description": "Engineering department group",
  "appliesTo": "all"
}'
```

**Response**

```json
{
  "id": "e980e881-b61f-11f0-a9b4-06fbd2118f4e",
  "name": "Test_group_10_31_11_37",
  "description": "Test group",
  "orgId": "64c9f048-afc1-49ab-aa1a-cf7920535831",
  "created": "2025-11-11T11:37:00Z",
  "type": "Federated",
  "appliesTo": "all"
}
```
