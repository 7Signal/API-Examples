# Rate Limiting

## 1. Overview

This document demonstrates how rate limiting works when using our API. Rate limiting ensures that the system resources are used reliably among users. This guide will explain what rate limits are, how to read the rate limit headers, and what to do if you exceed those limits.

Note: Rate limiting is enforced automatically. There is no setup required, however, it is important to understand how to monitor and respond to it.

## 2. What is Rate Limiting?

Rate limiting is an operation that restricts the number of API requests a client can make in a period of time. It essentially protects the system from an overload.

Analogy: Imagine there is a water cooler that refills over time. Each time you take a cup of water (an API request), you're using some of what is available in the cooler. If you take too many cups quickly, you will have to wait for the cooler to refill. Rate limiting is the same way — if you make too many requests too quickly, you will need to wait while it replenishes.

## 3. Rate Limit Summary

| **Field** | **Description** |
| --- | --- |
| `ratelimit-remaining` | How many requests you have left before the limit is hit |
| `ratelimit-burst-capacity` | Maximum number of tokens you can accumulate at once |
| `ratelimit-replenish-rate` | Number of tokens added per second back to the bucket |
| `ratelimit-requested-tokens` | Number of tokens this specific request used |

Applying the headers to the analogy:

- `ratelimit-burst-capacity` represents the maximum number of cups the water tank can hold — the total tokens available at once.
- `ratelimit-replenish-rate` is how quickly the cooler refills — the number of tokens added back per second.
- `ratelimit-remaining` is how many cups are still full — the tokens you have left to use right now.
- `ratelimit-requested-tokens` is the size of the cup you just took — how many tokens this request consumed.

## 4. How Rate Limiting Works

When making a request to the API:

1. The server first checks how many tokens (requests) you have available.
2. If you have enough tokens, the request is successful and the token count is reduced by `ratelimit-requested-tokens`.
3. If you do not have enough tokens, the request is rejected with a `429` error.
4. Over a period of time, the tokens are added back to the bucket at the rate defined by `ratelimit-replenish-rate`.

## 5. Example of Rate Limit Headers

A rate limit response includes the following headers:

```json
ratelimit-remaining: 7
ratelimit-burst-capacity: 15
ratelimit-replenish-rate: 5
ratelimit-requested-tokens: 1
```

This means:

- There are 7 tokens left
- The total capacity is 15 tokens
- You are regaining 5 tokens per second
- This request used 1 token

## 6. The 429 (Too Many Requests) Error

If you exceed the capacity, the server will respond with:

```json
HTTP/1.1 429 Too Many Requests
ratelimit-remaining: 0
ratelimit-burst-capacity: 15
ratelimit-replenish-rate: 5
ratelimit-requested-tokens: 1
```

You will have to wait before trying again. Your bucket will start to refill based on the replenish rate.

## 7. Handling Rate Limits

To keep the application dependable and avoid hitting the limits:

- Wait a few seconds before retrying
- Increase the wait time if the error still persists
- Check the `ratelimit-remaining` header to monitor usage
- Avoid unnecessary calls (cache responses where possible)

## 8. Example: Reading Rate Limit in Code

```python
response = requests.get("https://api-v2.7signal.com/resource")

print("Remaining:", response.headers.get("ratelimit-remaining"))
print("Burst Capacity:", response.headers.get("ratelimit-burst-capacity"))
print("Replenish Rate:", response.headers.get("ratelimit-replenish-rate"))
print("Tokens Used:", response.headers.get("ratelimit-requested-tokens"))
```

## 9. Troubleshooting & FAQs

**Q: What is the difference between `ratelimit-burst-capacity` and `ratelimit-remaining`?**

A: `burst-capacity` is the total limit of tokens; `remaining` is how many tokens you currently have left.

**Q: Can I increase my rate limits?**

A: Not by default. The API's rate limits are predefined based on the plan or account type you are using.

**Q: Can different API keys or users have different rate limits?**

A: Yes. Rate limits can vary depending on your account type.

**Q: What happens to the requests that go over the limit?**

A: Requests that exceed the limit are rejected immediately with a `429 Too Many Requests` error.

**Q: Will I get notified before hitting the limit?**

A: No. The only notification is the `ratelimit-remaining` header, which tells you how close you are to the limit.
