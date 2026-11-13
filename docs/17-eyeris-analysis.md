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

Analysis takes a few seconds to generate. `POST` returns as soon as the analysis has started, with the
identifiers you need to fetch it; `GET` then waits until the analysis is ready, for up to about 25 seconds,
so the first `GET` usually returns it.

## 2. Endpoints

#### `POST /eyeris/agents/client-analysis`

Starts an analysis. Returns `200` as soon as the analysis has started — **not** when it is finished.

**Required body fields:** `agentId`, `type`, `from`, `to`

**Optional parameters:** `organization`

```json
{
  "agentId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "type": "ROAMING",
  "from": 1740106800000,
  "to": 1740114000000
}
```

`from` and `to` are epoch milliseconds, as JSON numbers or numeric strings. The window must be longer than
zero and at most two hours, and Eyeris must be enabled for the organization; otherwise the request is
rejected with a `400` whose `message` says why.

Response:

```json
{
  "requestId": "8b1d4e77-0c25-4a63-9f18-5d2a7e6b3c90",
  "requestQueueId": "c47a2f10-9e83-4b51-a2d6-70f1b8c94e25"
}
```

Keep both values: `GET` needs `requestId` and `requestQueueId`. When an identical analysis has already
finished, it is reused and the response also carries its `responseId`.

#### `GET /eyeris/agents/client-analysis/{requestId}`

Fetches the result, waiting for it if it isn't ready yet.

**Required parameters:** `requestId` (UUID, in path) **and** `requestQueueId` (UUID, in query)

**Optional parameters:** `organization`. `responseId` is still accepted but no longer needed.

```
GET /eyeris/agents/client-analysis/8b1d4e77-0c25-4a63-9f18-5d2a7e6b3c90?requestQueueId=c47a2f10-9e83-4b51-a2d6-70f1b8c94e25
```

```json
{
  "response": "SUMMARY:\nThe client had one roaming failure, lasting 11 minutes, from 2026-02-21T01:51:00Z to 2026-02-21T02:02:00Z...\n\nANALYSIS:\n- Duration: ...\n- Primary Issue: ...\n- Secondary Factors: ...\n\nRECOMMENDATIONS:\nNetwork Optimization:\n- ...",
  "requestId": "8b1d4e77-0c25-4a63-9f18-5d2a7e6b3c90",
  "responseId": "e90f5c34-6b28-41d7-8a95-1f3c7d0b2a68"
}
```

The `response` field is plain text in three sections: `SUMMARY:`, `ANALYSIS:` and `RECOMMENDATIONS:`. Any
times inside it are ISO-8601 in UTC, for example `2026-02-21T13:00:00Z`. Some windows get a shorter answer:

- **Nothing failed:** a single sentence saying so, naming any SLA that wasn't measured.
- **Every failure lasted two minutes or less:** the full format, with `RECOMMENDATIONS:` saying no change is
  recommended because the failures were brief.
- **No data:** when the agent reported no data for that analysis type in the window, a single sentence such
  as `No roaming data was reported for this client between 2026-02-21T01:00:00Z and
  2026-02-21T03:00:00Z, so there is nothing to analyse for this period.`

The call waits until the analysis is ready, for up to about 25 seconds. If it ends without a result:

| Status | `message` | Meaning |
|---|---|---|
| `500` | `Eyeris analysis timed out` | Still generating when the call stopped waiting. Call `GET` again. |
| `500` | `Eyeris analysis failed` | The analysis failed. Start a new one with `POST`. |
| `404` | | The `requestId` and `requestQueueId` don't identify an analysis for your organization. |

#### `POST /eyeris/analysis/stream`

Runs an analysis and streams the text back as it is generated, using the
[Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
format (`Content-Type: text/event-stream`). The connection stays open until the analysis completes.

**Body fields:** `promptTypeKey`, `inputData`

**Prompt types:** `WIFI_CONGESTION_ANALYSIS`, `WIFI_COVERAGE_ANALYSIS`

Both prompt types take an agent time-series query as `inputData`: one agent's per-minute averages, split by
the BSSID it was connected to. Put the agent in `deviceIds`, and send `from` and `to` as epoch milliseconds.
`metrics` lists what the analysis reads; the congestion prompt type looks at `CONGESTION`,
`CHANNEL_UTILIZATION`, `CLIENT_COUNT`, `SIGNAL_STRENGTH` and `SEVEN_MCS`, and the coverage prompt type at
`COVERAGE`, `SIGNAL_STRENGTH`, `BEST_NEIGHBOR_SIGNAL_STRENGTH` and `SEVEN_MCS`.

```json
{
  "promptTypeKey": "WIFI_CONGESTION_ANALYSIS",
  "inputData": {
    "groupByDimension": "BSSID",
    "from": 1740106800000,
    "to": 1740114000000,
    "timeBucket": "ONE_MIN",
    "aggregateFunctions": ["AVG"],
    "metrics": ["CONGESTION", "CHANNEL_UTILIZATION", "CLIENT_COUNT", "SIGNAL_STRENGTH", "SEVEN_MCS"],
    "deviceIds": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
  }
}
```

The response is a sequence of SSE frames, each ending with a blank line. There are three kinds:

| Frame | Meaning |
|---|---|
| No `event:` line | A chunk of the analysis text. Join a frame's `data:` lines with newlines, then join chunks with nothing in between. |
| `event:progress` | The model has been called and text will follow. `data` is `{"stage":"generating"}`. A cached analysis skips this event. |
| `event:error` | The analysis stopped before it finished. `data` is `{"reason":"timeout"}` or `{"reason":"failed"}`. Any text received before it is **incomplete**. |

Lines starting with `:` (such as `:keepalive`) are comments that keep a quiet connection open. Ignore
them, along with any other named event you don't recognise: those are status updates, never analysis
text.

Keep everything after `data:` exactly as it is. The text is written straight after the colon, so a chunk
that begins with a space, as many do, keeps that space. Standard SSE clients such as the browser's
`EventSource` follow the SSE specification and remove one leading space after the colon, which runs words
together; read the frames yourself as shown below.

```
event:progress
data:{"stage":"generating"}

data:SUMMARY:
data:Congestion failed for 26 of 101 measured minutes

data: on the 2.4 GHz band.

```

The status code is `200` once the stream starts, so a failure part way through can't change it. It
arrives as an `error` event instead, after which the server closes the stream normally:

```
data:RECOMMENDATIONS:

event:error
data:{"reason":"timeout"}

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
| `INTERFERENCE` | Is co-channel or adjacent-channel interference degrading the experience? |

**`from` and `to` are epoch milliseconds**, at most two hours apart:

```python
import time

now_ms = int(time.time() * 1000)
two_hours_ago_ms = now_ms - (2 * 60 * 60 * 1000)

payload = {
    "agentId": agent_id,
    "type": "ROAMING",
    "from": two_hours_ago_ms,
    "to": now_ms,
}
```

**Fetching the result.** `GET` waits for the analysis, so the first call usually returns it. Call again
only when the call stopped waiting first, which it reports as a `500` whose `message` says it timed out; any
other error won't go away by retrying:

```python
for _ in range(4):
    result = get_analysis(token, request_id, request_queue_id)
    if result is not None:   # None: still generating when the call stopped waiting
        break
```

[`client_analysis.py`](../examples/eyeris/client_analysis.py) is the complete version.

**Consuming the stream in Python** needs `stream=True`, otherwise `requests` buffers the whole response
and you lose the incremental behaviour that makes the endpoint worth using. Read it frame by frame, so
that named events never end up in the analysis text:

```python
def read_sse_events(response):
    event_name, data_lines = None, []
    for line in response.iter_lines(decode_unicode=True):
        if line:
            if line.startswith("data:"):
                data_lines.append(line[len("data:"):])
            elif line.startswith("event:"):
                event_name = line[len("event:"):].strip()
            continue
        if data_lines:
            yield event_name, "\n".join(data_lines)
        event_name, data_lines = None, []
    if data_lines:
        yield event_name, "\n".join(data_lines)

with requests.post(url, headers=headers, json=payload, stream=True) as response:
    response.raise_for_status()
    chunks = []
    for event_name, data in read_sse_events(response):
        if event_name is None:
            chunks.append(data)
        elif event_name == "error":
            raise RuntimeError(f"Analysis incomplete: {json.loads(data)['reason']}")
    analysis = "".join(chunks)
```

[`analysis_stream.py`](../examples/eyeris/analysis_stream.py) is the complete version.

**Finding an agent ID:** agent UUIDs come from `/eyes/agents` — see [Eyes (Agents)](05-eyes-agents.md).

## 4. Troubleshooting & FAQs

**Q: `GET /eyeris/agents/client-analysis/{requestId}` returns `500` with "Eyeris analysis timed out".**

A: The analysis was still generating when the call stopped waiting, after about 25 seconds. Call `GET`
again with the same identifiers. If the message is "Eyeris analysis failed" instead, the analysis won't
finish: start a new one with `POST`.

**Q: `GET` returns `404`.**

A: The identifiers don't match an analysis for your organization. Check that you're passing the
`requestQueueId` that came back with the same `requestId`, and the same `organization` you used for `POST`.

**Q: I get a `400` and the analysis never starts.**

A: The `message` says why. Common causes: `type` sent in lowercase (it must be uppercase); a missing
required field — all four of `agentId`, `type`, `from`, and `to` are required; a window that is empty or
longer than two hours; or Eyeris not being enabled for the organization.

**Q: The analysis is a single sentence saying no data was reported.**

A: The agent reported no data for that analysis type during the window, so there was nothing to analyse.
Check the window covers a time the agent was active, and that the agent ID is the one you meant.

**Q: Do I have to pass `requestQueueId`? It isn't in the URL path.**

A: Yes. It's a required *query* parameter even though only `requestId` appears in the path. Omitting it
is the most common reason fetching the result fails.

**Q: The streaming endpoint takes a completely different body. Is that a mistake?**

A: No. `POST /eyeris/analysis/stream` takes `promptTypeKey` and an `inputData` object whose shape depends
on the prompt type, while `POST /eyeris/agents/client-analysis` takes the explicit
`agentId`/`type`/`from`/`to` fields. They are separate endpoints with separate contracts; don't assume a
payload built for one works on the other.

**Q: The stream returns `500` before any event arrives.**

A: Usually `inputData` is incomplete. Both prompt types need the whole time-series query —
`groupByDimension`, `from`, `to`, `timeBucket`, `aggregateFunctions`, `metrics` and `deviceIds` — as shown
in the example above.

**Q: My streamed output arrives all at once at the end.**

A: `stream=True` was almost certainly omitted from the request, so the HTTP client buffered the full
body before handing it over. Iterate with `iter_lines()` inside a `with` block as shown above.

**Q: Words in my streamed text run together.**

A: Your SSE client is removing the space after `data:`, as standard SSE clients do. Eyeris writes the text
straight after the colon, so that space belongs to the text. Read the frames yourself and keep everything
after `data:`, as shown in the Python example above.

**Q: My streamed text contains `{"stage":"generating"}` or `{"reason":"timeout"}`.**

A: The client is treating every `data:` line as analysis text. Those lines belong to the named `progress`
and `error` events. Track the `event:` line of each frame and only keep data from frames that have none,
as shown in the Python example above.

**Q: The stream closed normally, but the analysis stops mid-sentence.**

A: Check for an `error` event before the end of the stream. The analysis ran out of time (`timeout`) or
failed (`failed`) after the response had already started, so the status code is still `200` and the text
received up to then is incomplete. Request the analysis again rather than showing the partial text as
finished.

**Q: Can I re-read an analysis later instead of regenerating it?**

A: Yes, if you kept the identifiers. Call `GET /eyeris/agents/client-analysis/{requestId}` with the
original `requestQueueId`; a finished analysis comes back straight away.
