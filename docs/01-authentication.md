# Authentication

## 1. Overview

This document demonstrates how to authenticate with our API using an API Key and Secret. It is meant for technically proficient users, but they may not be familiar with Software Development. We will guide you through the process of acquiring a token, using it, and handling expiration.

Note: Instructions on how to acquire an API Key and Secret are provided separately (see [API Keys](04-api-keys.md)).

## 2. What is Authentication

Authentication ensures that only authorized users can access our API. You provide your API Key and Secret to the server in order to prove your identity. The server then gives you a token (a secure, temporary credential), which you will use for API requests.

Analogy: Authentication is similar to checking your ID at an event. When you show your ID (API Key and Secret), you get a wristband (token) that grants you access. Without it, you can't enter or do anything inside. Once you have your wristband, you no longer need to show your ID every time; the wristband alone is sufficient proof of access.

## 3. API Authentication Summary

| **Field** | **Description** |
| --- | --- |
| Endpoint | `POST https://api-v2.7signal.com/oauth/token` |
| Auth Type | Client Credentials (API key & Secret) |
| Token Format | JSON object with access token, expiry, and token type |
| Token Lifetime | 24 hours (86,400 seconds) |
| Required Header | `Authorization: Bearer <access_token>` |

## 4. How Authentication Works

1. Send your API Key and Secret to the authentication endpoint
   - An endpoint is a specific location on a server where an API client can send requests to access a resource or perform an action.
2. The server then checks your credentials.
3. If it is successful, you receive an access token.
4. You use this token for all future API requests.

## 5. Bearer Tokens

Bearer Tokens are a string that proves you are authorized, and you use it in your HTTP headers:

```json
Authorization: Bearer <your_token_here>
```

**Security Note:** If you save or persist your token, please take precautions to protect the token as anyone with access to it can use it to make API requests. Treat them as you would treat your passwords.

## 6. Reusing Tokens

Tokens are only valid for 24 hours. This amount of time is fixed and cannot be changed. Once you acquire a token, reuse it for the duration of its validity.

- Get a token once, and use it throughout the session
- Do not request a new token for every API call

## 7. Token Response

The token will expire automatically. The API response will include an `expires_in` field:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "scope": "read:resources write:resources",
  "expires_in": 86400,
  "token_type": "Bearer"
}
```

- `access_token`: The token you'll use in API requests.
- `scope`: The level of access that is granted by the token.
- `expires_in`: How long the token is valid, in seconds (86400 seconds = 24 hours).
- `token_type`: Usually "Bearer".

Once a token has expired, repeat the authentication process to get a new token.

## 8. Example: Making an API Call using the Token

Once you acquire a token, include it in the `Authorization` header of your API request:

**Example Request:**

```python
headers = {
    "Authorization": f"Bearer {token}"
}
api_url = "https://api-v2.7signal.com/resource"
response = requests.get(api_url, headers=headers)
print(response.json())
```

**Example Response:**

```json
{
  "token_type": "string",
  "access_token": "string",
  "expires_in": 86400,
  "refresh_token": "string"
}
```

## 9. Troubleshooting & FAQs

**Q: Why am I getting a 401 Unauthorized error?**

A: Possible reasons:
- Token is missing
- Token is expired
- Token is invalid

**Q: Why am I getting a 403 Forbidden error?**

A: Your token is valid, but does not have the required permissions.

**Q: What does "invalid_grant" mean in the authentication process?**

A: It usually means that the `grant_type` parameter is incorrect or missing. Make sure it is set to `client_credentials`.

**Q: What does "grant_type" mean?**

A: `grant_type` tells the server how you are trying to authenticate. For this specific API, use `client_credentials` to indicate you are using an authorization process with an API Key and Secret.

**Q: What is the difference between API Key and Client ID?**

A: If you're familiar with OAuth2, our API Key and Secret are just Client ID and Secret. We are using the same concept with simpler naming terms.
