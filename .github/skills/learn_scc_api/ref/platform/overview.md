# Platform Management

## Base URL

The platform management APIs use the global URL as the base URL. Do not use regional URLs for platform management APIs.

## About Organizations

The Organizations operations enable you to manage organizations within Security Cloud Control. You can create managed and standalone organizations, and update, retrieve, and list all types of organizations. Organizations support three types: STANDALONE, MANAGER, and MANAGED, allowing for flexible organizational hierarchies and multi-tenant management scenarios.

## About Subscriptions

The Subscriptions operations enable you to manage subscriptions for an organization within Security Cloud Control. You can list current subscriptions for an organization, get details for a specific subscription, add a subscription, modify an existing subscription, and activate or deactivate a subscription.

## About Claim Information

The ClaimInfo operation allows you to validate a claim code and retrieve details about the claim code for a specific organization.

## About Users

The Users operations allow you to perform actions on user accounts. You can list users or retrieve detailed user information. The PATCH operation can change the user account status to enable or disable the account, resend the email invite, reset the password, or reset multi-factor authentication (MFA). With PUT you can update a users first and last name within the organization.

## About User Groups

The User Group operation allows you to list all groups to which a specified user is assigned.

## About Admin Groups

The Admin Groups operations allow you to list all admin groups within an organization, list which organizations can access an admin group, view details for an admin group, add or remove users and managed organizations from an admin group, modify admin group details, and delete admin groups.

## About Roles

The Roles operations allow you to list roles, view details for a role, and assign or remove roles from users.

## About Refresh Token

The Security Cloud Control Refresh Token operation enables you to programmatically rotate your Security Cloud Control access token. You must have valid Security Cloud Control API key credentials to refresh your access token. For more information, see Authentication.

**Note:** Your Security Cloud Control API access token is valid for 18 hours.

The Security Cloud Control Refresh Token operation returns a valid access token that you can use to make requests to the Security Cloud Control API.

## API Specification

<https://pubhub.devnetcloud.com/media/cisco-security-cloud-control-api-documentation/docs/reference/cisco_security_cloud_control_platform_management_ap_is_1_0_3.yaml>
