# Errors and Troubleshooting

The Security Cloud Control API operations raise exceptions when a request has missing or invalid parameters, or formatting errors.

## Response Codes

The Security Cloud Control API uses HTTP response codes to indicate success or failure. In general, codes in the 2xx range indicate success. Codes in the 4xx range indicate an error that resulted from a syntax, name, or format errors. Codes in the 5xx range indicate server errors.

| Status Code | Status Message | Description |
|------------|----------------|-------------|
| 200 | OK | Success. Everything worked as expected. |
| 201 | Created | New resource created. |
| 202 | Accepted | Success. Action is queued. |
| 204 | No Content | Success. Response with no message body. |
| 400 | Bad Request | Likely missing a required parameter or malformed JSON. Review the syntax of your query. Check for any spaces preceding, trailing, or in the domain name of the domain you are trying to query. |
| 401 | Unauthorized | The authorization header is missing or the key and secret pair is invalid. Ensure that your API token is valid. |
| 403 | Forbidden | The client is unauthorized to access the content. |
| 404 | Not Found | The requested resource doesn't exist. Check the syntax of your query or ensure the IP and domain are valid. |
| 409 | Conflict | The client requests to create the resource, but the resource exists in the collection. |
| 429 | Exceeded Limit | Too many requests made within a specific time period. You may have exceeded the rate limits for your organization or package. |
| 413 | Content Too Large | The request payload is larger than the limits defined by the server. |
| 500 | Internal Server Error | Something wrong with the server. |
| 503 | Service Unavailable | Server is unable to complete request. |

If the response code is not specific enough to determine the cause of the issue, the server includes error messages in the response in JSON format.
