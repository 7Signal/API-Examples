# On-Demand Tests

## 1. Overview

On-demand tests allow you to trigger specific network performance tests on a sensor in real time. Each test type follows the same two-step pattern:

1. **POST** to start the test → receive a `testId`
2. **GET** to poll status until `runStatus` is `COMPLETE`, then read results

> **Related:** For packet capture specifically, see [Packet Capture](08-packet-capture.md).

## 2. Request Fields

All on-demand test POST requests share a common set of fields. The only required fields are `accessPointId` and `ipAddress`. Everything else has a sensible default. Most tests can be started with just these two fields:

```json
{
  "accessPointId": 1234,
  "ipAddress": {
    "ipProtocol": "IPV4"
  }
}
```

`useDhcp` defaults to `true`, so the above is sufficient for a standard DHCP network. Static IP and IPv6 fields only need to be set when DHCP is unavailable or a non-default configuration is required.

### Common Fields

| **Field** | **Type** | **Required** | **Default** | **Description** |
| --- | --- | --- | --- | --- |
| `accessPointId` | integer | Yes | — | Access point ID for the test. Retrieve from `GET /access-points/sensors`. |
| `ipAddress` | object | Yes | — | IP configuration (see below) |
| `testType` | string | No | `WLAN` | Network interface: `WLAN` or `Ethernet` |
| `maxAttachTimeoutMilliseconds` | integer | No | `20000` | Max time to wait for network attach |
| `maxIpAddressWaitTimeMilliseconds` | integer | No | `60000` | Max time to wait for IP address assignment |
| `customMacAddress` | string | No | `00:00:00:00:00:00` | Custom MAC address |

### IP Configuration (`ipAddress` object)

| **Field** | **Type** | **Required** | **Default** | **Description** |
| --- | --- | --- | --- | --- |
| `ipProtocol` | string | Yes | `IPV4` | `IPV4` or `IPV6` |
| `useDhcp` | boolean | No | `true` | Use DHCP for IP assignment |
| `localIpv4Address` | string | No | — | Static IPv4 address (when DHCP disabled) |
| `localNetworkMask` | string | No | — | IPv4 network mask (when DHCP disabled) |
| `gatewayIpv4Address` | string | No | — | IPv4 gateway address (when DHCP disabled) |
| `ipv6Mode` | string | No | `Automatic` | `Disabled`, `Automatic`, `Automatic with Stable Privacy`, `Automatic with Privacy Extensions (prefer public address)`, `Automatic with Privacy Extensions (prefer temporary address)`, `DHCPv6`, `Stateless DHCPv6`, or `Manual` |
| `localIpv6Address` | string | No | — | Static IPv6 address |
| `localIpv6Prefix` | string | No | — | IPv6 prefix |
| `gatewayIpv6Address` | string | No | — | IPv6 gateway address |

### DNS Overrides

The Web Download test also supports optional DNS server overrides:

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `dnsIpv4Server` | string | DNS IPv4 server address to use during the test |
| `dnsIpv6Server` | string | DNS IPv6 server address to use during the test |

### QoS Category

Several tests accept an optional `qosCategory` field:

| **Value** | **Description** |
| --- | --- |
| `BEST_EFFORT_0` | Best effort (default) |
| `BACKGROUND_1` | Background traffic |
| `VIDEO_5` | Video traffic |
| `VOICE_6` | Voice traffic |

## 3. Status Response

All GET status endpoints return:

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `testId` | string | Unique test identifier |
| `runStatus` | string | `IN_PROGRESS`, `COMPLETE`, or `ERROR` |
| `testStatus` | string | Test-specific status detail |
| `errorMessage` | string | Error description (only present if `runStatus` is `ERROR`) |
| `errorCode` | string | Error code (only present if `runStatus` is `ERROR`) |

When `runStatus` is `COMPLETE`, the response includes a `results` object with test-specific data. Most tests also include the following network timing fields in results:

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `attachTimeMilliseconds` | integer | Time taken to attach to the network |
| `ipRetrievalTimeMilliseconds` | integer | Time taken to obtain an IP address |
| `ipAddress` | string | IP address assigned during the test |
| `gatewayAddress` | string | Gateway address used during the test |

## 4. Test Types

---

### Ping

Tests ICMP reachability to a target host.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/ping`
- `GET /on-demand-tests/sensors/{sensorId}/ping/{testId}`

**Required:** `testEndpoint.testHost`. All other fields are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testEndpoint.testHost` | string | — | **(Required)** Hostname or IP to ping |
| `testEndpoint.testPort` | integer | — | Target port |
| `payloadSizeBytes` | integer | `32` | Ping payload size: `32`, `150`, `1450`, `9600`, or `64000` bytes |
| `intervalMilliseconds` | integer | `1000` | Interval between ping packets |
| `timeoutMilliseconds` | integer | `1000` | Timeout per ping request |
| `testCount` | integer | `10` | Number of ping requests to send |
| `qosCategory` | string | — | QoS category (see section 2) |

**Results (`pingResults` array):** Per-probe RTT and success/failure data.

---

### Ping Gateway

Tests ICMP reachability to the network gateway (no target host required).

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/ping-gateway`
- `GET /on-demand-tests/sensors/{sensorId}/ping-gateway/{testId}`

**No additional required fields.** All fields below are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `payloadSizeBytes` | integer | `32` | Ping payload size: `32`, `150`, `1450`, `9600`, or `64000` bytes |
| `intervalMilliseconds` | integer | `1000` | Interval between ping packets |
| `timeoutMilliseconds` | integer | `1000` | Timeout per ping request |
| `testCount` | integer | `10` | Number of ping requests to send |
| `qosCategory` | string | — | QoS category (see section 2) |

**Results (`pingResults` array):** Per-probe RTT and success/failure data to the gateway.

---

### HTTP Download

Measures download throughput via HTTP.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/http-download`
- `GET /on-demand-tests/sensors/{sensorId}/http-download/{testId}`

**Required:** `testEndpoint.testHost`. All other fields are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testEndpoint.testHost` | string | — | **(Required)** Hostname or IP of the HTTP server |
| `testEndpoint.testPort` | integer | — | Port of the HTTP server |
| `testEndpoint.sonarId` | string | — | Sonar server identifier |
| `testEndpoint.resolveDNSOnSensor` | boolean | — | Whether DNS resolution occurs on the sensor |
| `durationSeconds` | integer | `2` | Duration of the download test |
| `testCount` | integer | `1` | Number of download tests to perform |
| `qosCategory` | string | — | QoS category (see section 2) |
| `sonarDSCP` | integer | `0` | DSCP value for Sonar traffic |

**Results (`httpDownloadResults` array):** Per-test throughput measurements.

---

### HTTP Upload

Measures upload throughput via HTTP.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/http-upload`
- `GET /on-demand-tests/sensors/{sensorId}/http-upload/{testId}`

**Required:** `testEndpoint.testHost`. All other fields are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testEndpoint.testHost` | string | — | **(Required)** Hostname or IP of the HTTP server |
| `testEndpoint.testPort` | integer | — | Port of the HTTP server |
| `testEndpoint.sonarId` | string | — | Sonar server identifier |
| `testEndpoint.resolveDNSOnSensor` | boolean | — | Whether DNS resolution occurs on the sensor |
| `durationSeconds` | integer | `2` | Duration of the upload test |
| `testCount` | integer | `1` | Number of upload tests to perform |
| `qosCategory` | string | — | QoS category (see section 2) |
| `sonarDSCP` | integer | `0` | DSCP value for Sonar traffic |

**Results (`httpUploadResults` array):** Per-test throughput measurements.

---

### Speedtest

Runs an Ookla-based internet speedtest.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/speedtest`
- `GET /on-demand-tests/sensors/{sensorId}/speedtest/{testId}`

**No additional required fields.** The test server is auto-selected and parallel connections are auto-configured. All fields below are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testServerId` | integer | — | Specific Ookla speedtest server ID. Omit to auto-select. |
| `downloadConnectionRangeMin` | integer | `0` | Minimum parallel connections for download |
| `downloadConnectionRangeMax` | integer | `0` | Maximum parallel connections for download |
| `uploadConnectionRangeMin` | integer | `0` | Minimum parallel connections for upload |
| `uploadConnectionRangeMax` | integer | `0` | Maximum parallel connections for upload |

**Results:** Download/upload throughput, ping stats, server details, and interface information.

---

### Traceroute

Maps the network path to a target host hop by hop.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/traceroute`
- `GET /on-demand-tests/sensors/{sensorId}/traceroute/{testId}`

**Required:** `testEndpoint.testHost`. All other fields are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testEndpoint.testHost` | string | — | **(Required)** Hostname or IP address to trace |
| `testEndpoint.testPort` | integer | — | Target port |
| `minimumTtl` | integer | `1` | Starting TTL (hop count) |
| `maximumTtl` | integer | `255` | Maximum TTL (hop count) |
| `queriesPerHop` | integer | `5` | Probe packets sent per hop |
| `timeoutMilliseconds` | integer | `2000` | Timeout per probe |
| `testTimeoutSeconds` | integer | `20` | Overall test timeout |
| `qosCategory` | string | — | QoS category (see section 2) |

**Results (`traceRouteResults` array):** Hop-by-hop entries with RTT and TTL arrays.

---

### iPerf3

Runs a configurable iPerf3 throughput test against an iPerf3 server.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/iperf3`
- `GET /on-demand-tests/sensors/{sensorId}/iperf3/{testId}`

**Required:** `testEndpoint` (the server hostname or IP). All other fields are optional — iPerf3 has the most configuration options of any test type, but defaults cover a standard 10-second TCP throughput test.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testEndpoint` | string | — | **(Required)** Hostname or IP of the iPerf3 server |
| `testEndpointPort` | integer | `5201` | Port of the iPerf3 server |
| `sendTimeSeconds` | integer | `10` | Test duration in seconds |
| `targetBitRateBps` | integer | — | Target bitrate in bits per second |
| `testIntervalSeconds` | integer | `1` | Interval between bandwidth reports |
| `testConnectTimeoutMilliseconds` | integer | `2000` | Connection timeout |
| `bufferLengthBytes` | integer | `128000` | Buffer size |
| `windowSizeBytes` | integer | — | TCP window size |
| `congestionControl` | string | — | TCP congestion control algorithm (e.g., `reno`) |
| `maxSegmentSizeBytes` | integer | — | Maximum TCP segment size |
| `ipTos` | integer | `0` | IP Type of Service. Mutually exclusive with `dscp`. |
| `dscp` | string | — | DSCP value. Mutually exclusive with `ipTos`. |
| `omitSeconds` | integer | — | Seconds to omit from start of test |
| `pacingTimerMicroseconds` | integer | — | Pacing timer in microseconds |
| `fairQueueRateBps` | integer | — | Fair queue rate in bits per second |
| `sendBytes` | integer | — | Total bytes to send (alternative to `sendTimeSeconds`) |
| `sendBlocks` | integer | — | Number of blocks to send |
| `useUDP` | boolean | `false` | Use UDP instead of TCP |
| `reverseDirection` | boolean | `false` | Reverse test direction (server sends to sensor) |
| `bidirectional` | boolean | `false` | Run bidirectional test |
| `dontFragment` | boolean | `false` | Set the IP don't-fragment flag |
| `noDelay` | boolean | `false` | Disable Nagle's algorithm |
| `zeroCopy` | boolean | `false` | Use zero-copy mode |

**Results:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `transferredBytes` | integer | Total bytes transferred |
| `throughputMbps` | number | Measured throughput in Mbps |
| `rawIperf3Output` | object | Raw iPerf3 JSON output |

---

### MOS (VoIP Quality)

Simulates VoIP traffic and measures Mean Opinion Score.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/mos`
- `GET /on-demand-tests/sensors/{sensorId}/mos/{testId}`

**Required:** `testHost`. All other fields are optional, with codec and direction defaulting to `PCM_LINEAR_16` downlink.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testHost` | string | — | **(Required)** Hostname or IP of the MOS test server |
| `testPort` | integer | — | Target port |
| `direction` | string | `DOWNLINK` | `UPLINK` or `DOWNLINK` |
| `codec` | string | `PCM_LINEAR_16` | `PCM_LINEAR_16` (188-byte packets) or `GSM` (48-byte packets) |
| `fec` | string | `NO_FEC` | Forward error correction: `NO_FEC`, `GSM_PIGGYBACK_OFFSET_1`, `GSM_PIGGYBACK_OFFSET_2`, `GSM_PIGGYBACK_OFFSET_3` |
| `qosCategory` | string | — | QoS category (see section 2) |
| `sonarDSCP` | integer | `0` | DSCP value for Sonar traffic |
| `sender` | object | — | Sender configuration |
| `receiver` | object | — | Receiver configuration |

**Results (`voipResults` array):** MOS scores, jitter, and packet loss rates.

---

### UDP Download

Measures download throughput over UDP.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/udp-download`
- `GET /on-demand-tests/sensors/{sensorId}/udp-download/{testId}`

**No additional required fields.** All fields below are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `downloadMegabytes` | string | `FOUR` | Payload size: `ONE`, `FOUR`, `TEN`, `HUNDRED`, `TWOHUNDRED`, `FIVEHUNDRED` |

**Results (`udpDownloadResults` array):** Per-test throughput and packet loss data.

---

### UDP Upload

Measures upload throughput over UDP.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/udp-upload`
- `GET /on-demand-tests/sensors/{sensorId}/udp-upload/{testId}`

**No additional required fields.** All fields below are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `uploadMegabytes` | string | `FOUR` | Payload size: `ONE`, `FOUR`, `TEN`, `HUNDRED`, `TWOHUNDRED`, `FIVEHUNDRED` |

**Results (`udpUploadResults` array):** Per-test throughput and packet loss data.

---

### TCP Download

Measures download throughput over TCP.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/tcp-download`
- `GET /on-demand-tests/sensors/{sensorId}/tcp-download/{testId}`

**No additional required fields.** All fields below are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `downloadMegabytes` | string | `FOUR` | Payload size: `ONE`, `FOUR`, `TEN`, `HUNDRED`, `TWOHUNDRED`, `FIVEHUNDRED` |

**Results (`tcpDownloadResults` array):** Per-test throughput measurements.

---

### TCP Upload

Measures upload throughput over TCP.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/tcp-upload`
- `GET /on-demand-tests/sensors/{sensorId}/tcp-upload/{testId}`

**No additional required fields.** All fields below are optional.

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `uploadMegabytes` | string | `FOUR` | Payload size: `ONE`, `FOUR`, `TEN`, `HUNDRED`, `TWOHUNDRED`, `FIVEHUNDRED` |

**Results (`tcpUploadResults` array):** Per-test throughput measurements.

---

### Web Download

Downloads one or more web pages and measures page load performance.

**Endpoints:**
- `POST /on-demand-tests/sensors/{sensorId}/web-download`
- `GET /on-demand-tests/sensors/{sensorId}/web-download/{testId}`

**No additional required fields.** Provide `testHosts` to test specific URLs; omit to use a predefined server. DNS server overrides are also supported for this test type (see DNS Overrides in section 2).

**Additional Request Fields:**

| **Field** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| `testHosts` | string[] | — | List of URLs or hostnames to test (e.g., `["www.google.com"]`) |
| `timeoutSeconds` | integer | `60` | Maximum test duration |
| `webServerId` | integer | — | Optional predefined web server identifier |
| `proxyServerUrl` | string | — | Proxy server URL (e.g., `http://proxy.example.com:8080`) |
| `resolveDNSOnSensor` | boolean | `false` | Whether DNS resolution occurs on the sensor |

**Results:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `sentPackets` | integer | Total packets sent |
| `receivedPackets` | integer | Total packets received |
| `sentPacketRetransmissionCount` | integer | Retransmitted packets on send |
| `receivedPacketRetransmissionCount` | integer | Retransmitted packets on receive |
| `averageFrameSize` | integer | Average frame size in bytes |
| `minimumFrameSize` | integer | Minimum frame size in bytes |
| `maximumFrameSize` | integer | Maximum frame size in bytes |
| `webDownloadResults` | array | Per-URL download results |

---

## 5. Listing Active Tests

### `GET /on-demand-tests/sensors/active-tests`

Returns metadata for on-demand tests already submitted on a sensor, so you can see what is queued or
running before submitting another. Tests do not start while an automated test is running on the sensor, so
this is the endpoint to check when a test appears to be doing nothing.

**Required parameters:** `sensorId` **and** `testType` — unlike the other endpoints on this page, both are
mandatory query parameters. You cannot list active tests across all sensors or all test types in one call.

**Optional parameters:** `channel`, `apId`, `band`, `start`, `end`, `page`, `size`

| **Parameter** | **Type** | **Description** |
| --- | --- | --- |
| `sensorId` | integer | **Required.** The sensor to list tests for |
| `testType` | string | **Required.** One of `PING`, `HTTP_DOWNLOAD`, `HTTP_UPLOAD`, `IPERF3`, `SPEEDTEST`, `TRACEROUTE`, `MOS`, `UDP_DOWNLOAD`, `UDP_UPLOAD`, `TCP_DOWNLOAD`, `TCP_UPLOAD`, `WEB_DOWNLOAD` |
| `channel` | integer | Filter by Wi-Fi channel number |
| `apId` | integer | Filter by access point ID |
| `band` | string | `2.4`, `5`, `6`, or `all` |
| `start` | integer | Start of time range (epoch milliseconds) |
| `end` | integer | End of time range (epoch milliseconds) |
| `page` | integer | **Zero-based** page number (default `0`) |
| `size` | integer | Page size (default `20`) |

> **Pagination differs from the rest of this API.** This endpoint uses **0-based** `page` numbering and a
> `size` parameter, and the results array is named `items` rather than `results`. Most other endpoints use
> 1-based `page` with `perPage` and a `results` array.

**Response:**

```json
{
  "pagination": {
    "perPage": 20,
    "page": 0,
    "total": 3,
    "pages": 1
  },
  "items": [
    {
      "id": "f0c8a3d1-6b74-4e29-9a5c-31d7b8e05f62",
      "testKey": "5c9a1e84-2f70-4b3d-8e16-7a0c4d9b2f58",
      "testId": 884213,
      "testType": "SPEEDTEST",
      "sensorId": 1042,
      "sensorUuid": "9d3f7c20-8a15-4e62-b7d9-40c1e6a85b73",
      "sensorName": "Eye-Cleveland-03",
      "orgUuid": "2b7e4a90-1c58-4d37-8f26-93a0c5e71d84",
      "apId": 5517,
      "band": "5",
      "channel": 36,
      "gid": 12,
      "resultsFileS3Key": "results/884213.json",
      "runStatus": "IN_PROGRESS",
      "errorCode": 0,
      "errorMessage": null,
      "testStatus": null,
      "createdAt": "2026-08-18T13:04:11Z",
      "hostname": "eye-cle-03"
    }
  ]
}
```

**Field notes:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| `testId` | integer | The numeric id used by the per-test-type `GET .../{testId}` status endpoints |
| `testKey` | string | UUID key for the test |
| `runStatus` | string | `IN_PROGRESS`, `COMPLETE`, or `ERROR` |
| `errorCode` | integer | `0` means no error |
| `band` | string | `2.4`, `5`, `6`, or `N/A` |
| `createdAt` | string | ISO-8601, UTC |

Filter on `runStatus` of `IN_PROGRESS` client-side to see only what is still outstanding — the endpoint
returns recent test metadata regardless of status rather than exclusively in-flight tests.

---

## 6. Developer Tips

- Always capture the `testId` from the POST response — it is the only way to retrieve results.
- Poll the GET status endpoint at a reasonable interval (e.g., every 5 seconds). Tests do not start immediately if an automated test is running on the sensor.
- Retrieve `sensorId` from `GET /eyes/sensors`.
- Retrieve `accessPointId` from `GET /access-points/sensors`.
- Check `runStatus` before reading `results` — results are only present when `runStatus` is `COMPLETE`.
- If `runStatus` is `ERROR`, inspect `errorMessage` and `errorCode` for details.
