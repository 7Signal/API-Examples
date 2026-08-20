# Eyeris Analysis

## 1. Overview

Eyeris produces an AI-generated, natural-language explanation of what a given agent's Wi-Fi experience
looked like over a time window. Instead of returning metrics for you to interpret, it returns prose: a
summary of what happened, the likely cause, and recommendations.

You choose one of four analysis types — roaming, congestion, coverage, or interference — and give it an
agent and a time range. The analysis is intended to shorten troubleshooting for anyone, regardless of how
deep their RF knowledge goes.

There are two ways to consume it, and they are genuinely different endpoints rather than variations of one:

| | Request/poll | Streaming |
|---|---|---|
| Endpoints | `POST /eyeris/agents/client-analysis` then `GET .../{requestId}` | `POST /eyeris/analysis/stream` |
| Response | JSON, complete when ready | Server-Sent Events, arrives in chunks |
| Body shape | `agentId` + `type` + `from` + `to` | `promptTypeKey` + `inputData` |
| Best for | Scripts, batch jobs, anything that can wait | Interactive UIs showing text as it generates |

Analysis takes time to generate. The request/poll endpoints exist precisely so your client isn't holding
a connection open while it runs — `POST` returns immediately with identifiers, and you poll until the
result is ready.

## 2. Endpoints

#### `POST /eyeris/agents/client-analysis`

Starts an analysis. Returns `201` as soon as Eyeris has accepted the request — **not** when the analysis
is finished.

**Required body fields:** `agentId`, `type`, `from`, `to`

**Optional parameters:** `organization`

```json
{
  "agentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "type": "ROAMING",
  "from": "1740106800000",
  "to": "1740114000000"
}
```

Response:

```json
{
  "requestId": "8b1d4e77-0c25-4a63-9f18-5d2a7e6b3c90",
  "requestQueueId": "c47a2f10-9e83-4b51-a2d6-70f1b8c94e25",
  "responseId": "e90f5c34-6b28-41d7-8a95-1f3c7d0b2a68"
}
```

Keep all three values. `requestId` and `requestQueueId` are both needed to poll; `responseId` is
optional but makes the lookup more direct when present.

#### `GET /eyeris/agents/client-analysis/{requestId}`

Polls for the result.

**Required parameters:** `requestId` (UUID, in path) **and** `requestQueueId` (UUID, in query)

**Optional parameters:** `responseId`, `organization`

```
GET /eyeris/agents/client-analysis/8b1d4e77-0c25-4a63-9f18-5d2a7e6b3c90?requestQueueId=c47a2f10-9e83-4b51-a2d6-70f1b8c94e25
```

```json
{
  "response": "# Wi-Fi Network Analysis\n\n## SUMMARY\nThe device experienced a brief 2-minute connectivity problem...\n\n## RECOMMENDATIONS\nNo device-side changes are recommended...",
  "requestId": "8b1d4e77-0c25-4a63-9f18-5d2a7e6b3c90",
  "responseId": "e90f5c34-6b28-41d7-8a95-1f3c7d0b2a68"
}
```

The `response` field is Markdown-formatted text. Any dates inside it are ISO-8601 in UTC, for example
`2026-02-21T13:00:00Z`.

Returns `404` while the analysis is still being generated, so treat `404` as "not ready yet, poll again"
rather than as a hard failure.

#### `POST /eyeris/analysis/stream`

Runs an analysis and streams the text back as it is generated, using the
[Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
format (`Content-Type: text/event-stream`). The connection stays open until the analysis completes.

**Body fields:** `promptTypeKey`, `inputData`

```json
{
  "promptTypeKey": "ROAMING",
  "inputData": {
    "agentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "from": "1740106800000",
    "to": "1740114000000"
  }
}
```

The response is a sequence of `data:` lines:

```
data:# Wi-Fi Network Analysis
data:
data:## SUMMARY
data:The device experienced a brief 2-minute connectivity problem
data:
data:## RECOMMENDATIONS
data:
data:No device-side changes are recommended. The brief disruption followed by sustained 100% SLA indicates normal operation was quickly established and maintained.
```

The same three identifiers come back as **response headers** rather than in the body:
`Eyeris-Request-Id`, `Eyeris-Request-Queue-Id`, and `Eyeris-Response-Id`.

## 3. Developer Tips

**Analysis types are UPPERCASE.** The `type` field accepts exactly `ROAMING`, `CONGESTION`, `COVERAGE`,
or `INTERFERENCE`. Lowercase is rejected with a `400`.

> Worth noting if you also use the [Alerting](16-alerting.md) endpoints: those enums are lowercase
> (`avg`, `ignore`), while these are uppercase. The two resources do not share a convention.

| Type | Answers |
|------|---------|
| `ROAMING` | Is the device handing off between APs cleanly, or sticking/flapping? |
| `CONGESTION` | Is contention for airtime degrading the experience? |
| `COVERAGE` | Is the device seeing usable signal where it's being used? |
| `INTERFERENCE` | Is non-Wi-Fi or co-channel interference degrading the channel? |

**`from` and `to` are epoch milliseconds sent as JSON strings**, not integers:

```python
import time

now_ms = int(time.time() * 1000)
two_hours_ago_ms = now_ms - (2 * 60 * 60 * 1000)

payload = {
    "agentId": agent_id,
    "type": "ROAMING",
    "from": str(two_hours_ago_ms),   # string, not int
    "to": str(now_ms),
}
```

**Polling pattern.** Poll with a fixed interval and a retry ceiling, and treat `404` as "still working":

```python
for _ in range(60):
    result = get_analysis(token, request_id, request_queue_id)
    if result is not None:
        break
    time.sleep(5)
```

**Consuming the stream in Python** needs `stream=True`, otherwise `requests` buffers the whole response
and you lose the incremental behaviour that makes the endpoint worth using:

```python
with requests.post(url, headers=headers, json=payload, stream=True) as response:
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if line and line.startswith("data:"):
            logging.info(line[len("data:"):])
```

**Finding an agent ID:** agent UUIDs come from `/eyes/agents` — see [Eyes (Agents)](05-eyes-agents.md).

## 4. Troubleshooting & FAQs

**Q: `GET /eyeris/agents/client-analysis/{requestId}` returns `404` right after the `POST` succeeded.**

A: That's expected. The analysis isn't ready yet. Keep polling — `404` here means "not yet", not "wrong
id". If it never resolves, re-check that you're passing `requestQueueId` as well as `requestId`.

**Q: I get a `400` and the analysis never starts.**

A: Three common causes, in order of likelihood: `type` sent in lowercase (it must be uppercase); `from`
or `to` sent as JSON numbers instead of strings; or a missing required field — all four of `agentId`,
`type`, `from`, and `to` are required.

**Q: Do I have to pass `requestQueueId`? It isn't in the URL path.**

A: Yes. It's a required *query* parameter even though only `requestId` appears in the path. Omitting it
is the most common reason polling fails. `responseId` is the genuinely optional one.

**Q: The streaming endpoint takes a completely different body. Is that a mistake?**

A: No. `POST /eyeris/analysis/stream` takes `promptTypeKey` and a free-form `inputData` object, while
`POST /eyeris/agents/client-analysis` takes the explicit `agentId`/`type`/`from`/`to` fields. They are
separate endpoints with separate contracts; don't assume a payload built for one works on the other.

**Q: My streamed output arrives all at once at the end.**

A: `stream=True` was almost certainly omitted from the request, so the HTTP client buffered the full
body before handing it over. Iterate with `iter_lines()` inside a `with` block as shown above.

**Q: Can I re-read an analysis later instead of regenerating it?**

A: Yes, if you kept the identifiers. Poll `GET /eyeris/agents/client-analysis/{requestId}` with the
original `requestQueueId`, and supply `responseId` too when you have it — the server can then locate a
cached response directly rather than searching for it.
