# Getting Started with Security Cloud Control

This guide will walk you through the initial setup steps to access Cisco Security Cloud Control (SCC) and configure API access for both:
- **SCC Admin API** - User management, group management, role assignments, and organizational administration
- **FMC API** - Firewall Management Center operations (device management, policies, objects, VPN monitoring)

## Prerequisites

Before you begin, ensure you have valid credentials for Cisco Security Platform.

## Step 1: Log In to Security Cloud Control

1. Navigate to the [Cisco Security Platform](https://security.cisco.com)
2. Enter your credentials and log in
3. Once authenticated, you'll have access to the platform dashboard

## Step 2: Find Your Organization ID

Your Organization ID is required for API authentication and management operations.

1. From the main dashboard, click **Platform Management**
2. Select **Organization Details**
3. On the Organization Details page, locate and copy your **Organization ID**
4. Save this ID securely - you'll need it for API configuration

## Step 3: Create API Keys

Security Cloud Control uses different API keys for different operations:

### API Key Types

**SCC Admin API Key** - For organizational administration:
- User management, group management, role assignments
- Organizational settings and configuration
- Uses endpoint: `https://api.security.cisco.com/v1/`

**FMC API Key** - For Firewall Management Center operations:
- Device management, policy configuration, object management
- cdFMC operations, VPN monitoring, deployments
- Uses endpoint: `https://api.{region}.security.cisco.com/firewall`

### Generate Your API Keys

1. Navigate to **Platform Management**
2. Click on **API Keys**
3. Click **Generate an API key**
4. Fill in the required information:
   - Provide a descriptive name (e.g., "SCC Admin API" or "FMC API")
   - Set appropriate permissions based on your needs
5. Click **Generate**
6. **Important**: Copy the **Access Token** immediately
   - This token will only be displayed once
   - Store it securely - you won't be able to retrieve it again
7. **Repeat** this process if you need both SCC Admin and FMC access

> **Note**: You may only need one type of API key depending on your use case:
> - **SCC Admin only**: If you're managing users, groups, and roles
> - **FMC only**: If you're managing firewalls, devices, and policies
> - **Both**: If you need full organizational and firewall management capabilities

## Step 4: Configure Your Environment

Now that you have your Organization ID and API Access Tokens, configure your local environment:

### Set Up hosts.sh

1. Copy the example configuration file:
   ```bash
   cp hosts.sh.example hosts.sh
   ```

2. Edit `hosts.sh` and update the following values:
   
   **Organization ID (Required for both APIs):**
   ```bash
   SCC_ORG_UUID="00000000-0000-0000-0000-000000000000"
   ```
   Replace with the Organization ID you copied in Step 2.

   **SCC Admin API Access Token (for user/group management):**
   ```bash
   SCC_API_KEY="REPLACE_WITH_ADMIN_ACCESS_TOKEN"
   ```
   Replace with the Access Token you generated for SCC Admin operations.

   **FMC API Access Token (for firewall operations):**
   ```bash
   SCC_FMC_API_KEY="REPLACE_WITH_FMC_ACCESS_TOKEN"
   SCC_EDGE_URL="https://api.us.security.cisco.com/firewall"
   ```
   Replace with the Access Token you generated for FMC operations.
   Update the URL to match your deployment region (us, eu, apj, au, in, uae).

   **Optional - Organization Display Name:**
   ```bash
   SCC_ORG_ID="Your Org Display Name"
   ```
   You can update this with your organization's friendly name for reference.

3. Load the configuration into your environment:
   ```bash
   set -a; source hosts.sh; set +a
   ```

4. **Important**: Never commit `hosts.sh` with real credentials to version control
   - The file is already in `.gitignore` (if present)
   - Only `hosts.sh.example` should be committed

## Next Steps

Once you have configured your environment, you can:

**With SCC Admin API (SCC_API_KEY):**
- Use the SCC SDK for programmatic access
- Automate user management, group management, and role assignments
- Run SCC administrative scripts and tools
- Manage organizational settings

**With FMC API (SCC_FMC_API_KEY):**
- Manage firewall devices and device managers (cdFMC)
- Configure policies, network objects, and security rules
- Monitor Remote Access VPN sessions
- Deploy configuration changes to devices
- Run firewall automation scripts

## Security Best Practices

- Never share your API tokens
- Never commit `hosts.sh` with real credentials to version control
- Rotate API keys regularly according to your organization's security policy
- Store credentials securely (environment variables, secrets management tools)
- Use the principle of least privilege when generating API keys
- Generate separate API keys for SCC Admin and FMC operations for better security isolation
