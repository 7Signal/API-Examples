# Sensor Targets, Network Keys & Default Configurations

## 1. Overview

These three resources are the configuration that sensors (Eyes) test *against* and connect *with*:

- **Targets** (`/targets/sensors`) — the endpoints a sensor tests toward: a Sonar server, a web server,
  a ping endpoint, or an iPerf3 server. Test profiles reference targets by id.
- **Network keys** (`/network-keys/sensors`) — the credentials and authentication settings a sensor uses
  to associate to a wireless network. Everything from a WPA2 passphrase to full 802.1X/EAP with
  certificates, SCEP enrolment, or captive-portal form filling.
- **Default configurations** (`/default-configurations/sensors`) — read-only bundles that group a test
  profile template, OTA configuration, alarm group, SLA group, and target references together. Service
  Areas and Organizations point at one of these by `defaultConfigurationId`.

Targets and network keys are fully writable. Default configurations are read-only through this API — you
can list them and read them, but they're assembled elsewhere.

Two things apply to both writable resources and are worth internalising before you start:

1. **`PUT` is a full replace, not a patch.** Send the complete desired state every time.
2. **Ids here are integers**, not UUIDs — unlike agents, locations, and alert rules elsewhere in this API.

## 2. Endpoints

### Sensor Targets

#### `GET /targets/sensors`

Pages through the organization's sensor targets.

**Required parameters:** none

**Optional parameters:** `organization`, `page`, `perPage`, `sortField`, `order`

```json
{
  "results": [
    {
      "id": 412,
      "name": "Corporate Sonar",
      "description": "Primary Sonar server in the Cleveland datacenter",
      "targetType": "SONAR",
      "tcpPort": 80,
      "dnsName": "sonar.example.com",
      "ipV4Address": "10.20.30.40",
      "ipV6Address": null
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 7,
    "pages": 1
  }
}
```

#### `POST /targets/sensors`

Creates a target and returns it.

**Required fields:** `targetType`, `name` — plus an address, which varies by type:

| `targetType` | Address requirement | `tcpPort` |
|--------------|--------------------|-----------|
| `WEB_SERVER` | `dnsName` required | ignored |
| `IPERF3_SERVER` | `dnsName` required | optional, defaults to `5201` |
| `SONAR` | at least one of `dnsName` / `ipV4Address` / `ipV6Address` | optional, defaults to `80` |
| `PING_ENDPOINT` | at least one of `dnsName` / `ipV4Address` / `ipV6Address` | ignored |

```json
{
  "targetType": "IPERF3_SERVER",
  "name": "Branch iPerf3",
  "description": "Throughput target for branch offices",
  "dnsName": "iperf.example.com",
  "tcpPort": 5201
}
```

**`targetType` cannot be changed after creation.** To change a target's kind, delete it and create a new
one.

#### `GET /targets/sensors/{targetId}`

**Required parameters:** `targetId` (integer, in path)

#### `PUT /targets/sensors/{targetId}`

Replaces the target and returns it. `targetType` is not part of the update.

**Required fields:** `name`, plus the same per-type address requirement as `POST`.

`dnsName`, `ipV4Address`, and `ipV6Address` **fully replace** their existing values — omitting one clears
it. If a `SONAR` target currently has both a DNS name and an IPv4 address and you `PUT` only the DNS
name, the IPv4 address is removed.

#### `DELETE /targets/sensors/{targetId}`

Returns `204`. Fails if the target is still referenced by a test profile — detach it there first.

### Sensor Network Keys

#### `GET /network-keys/sensors`

Pages through the organization's network keys.

**Optional parameters:** `organization`, `page`, `perPage`, `sortField`, `order`

```json
{
  "results": [
    {
      "id": 88,
      "name": "Corporate WPA2",
      "type": "WPA2",
      "usePassphrase": true,
      "passphraseOrPsk": "********",
      "customFields": []
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 12,
    "pages": 2
  }
}
```

#### `POST /network-keys/sensors`

Creates a network key. **Required fields: `type` and `name`.** Every other field's applicability is
determined by `type` — the request shape is effectively resolved from it.

```json
{
  "type": "WPA2",
  "name": "Corporate WPA2",
  "usePassphrase": true,
  "passphraseOrPsk": "correct-horse-battery-staple"
}
```

Available `type` values:

| Type | Use |
|------|-----|
| `WPA1`, `WPA2` | Pre-shared key. `usePassphrase` selects passphrase vs. raw hex PSK |
| `WPA3` | Pre-shared key. `pure` selects WPA3-only vs. mixed WPA3/WPA2-PSK |
| `WPA3_OWE` | Opportunistic Wireless Encryption — no shared secret at all |
| `WPA_EAP` | WPA with 802.1X/EAP. `eapMethod` selects the variant |
| `WPA_EAP_SCEP` | WPA/EAP where the sensor enrols its own certificate via SCEP |
| `IEEE_802_1X` | Wired/WPA-less 802.1X. `eapMethod` selects the variant |
| `OPEN_HTTP` | Open SSID with an HTTP POST authentication step |
| `HTTP_AUTHENTICATION` | Captive portal — scripted login/logout form sequences |
| `RAW` | A raw `wpa_supplicant.conf`-style block in `keyFileContent` |

`eapMethod` (for `WPA_EAP` and `IEEE_802_1X`) accepts `EAP_TLS`, `EAP_PEAP`, `EAP_TTLS`, `EAP_PSK`,
`EAP_FAST`, `LEAP`, or `EAP_MSCHAP_V2`, and each brings its own relevant fields — identity, inner
authentication method, certificates, and so on.

Because the field matrix is large and strictly conditional, the
[Swagger UI](https://api-v2.7signal.com/swagger-ui/index.html) is the authoritative per-type reference.
It carries a worked request example for each `type`.

#### `GET /network-keys/sensors/templates`

Lists the pre-built network key templates. These exist to give you a working starting point for
`HTTP_AUTHENTICATION` keys, whose login-page field sequences are tedious to build from nothing.

**Optional parameters:** `organization`

Fetch a template, adapt it, then `POST` it as a new key.

#### `GET /network-keys/sensors/{networkKeyId}`

**Required parameters:** `networkKeyId` (integer, in path)

#### `PUT /network-keys/sensors/{networkKeyId}`

Full replace — "provide the complete desired state on every call." See the round-trip warning in
Developer Tips before building an edit flow on top of this.

**Required parameters:** `networkKeyId` (integer, in path)

#### `DELETE /network-keys/sensors/{networkKeyId}`

Returns `204`. Returns `409` if the key is still bound to a wireless network or a sensor — unbind it
first.

### Sensor Default Configurations

#### `GET /default-configurations/sensors`

Lists the configuration bundles that a Service Area or Organization can reference via
`defaultConfigurationId`.

**Optional parameters:** `organization`, `page`, `perPage`, `sortField`, `order`

```json
{
  "results": [
    {
      "id": 5,
      "name": "Standard Branch Office",
      "testProfileTemplateId": 22,
      "otaConfigurationId": 3,
      "alarmGroupId": 9,
      "sonarId": 412,
      "pingEndPointId": 415,
      "webServerId": 417,
      "slaGroupId": 2
    }
  ],
  "pagination": {
    "perPage": 10,
    "page": 1,
    "total": 4,
    "pages": 1
  }
}
```

Every id field is optional — a bundle that doesn't apply an alarm group simply has no `alarmGroupId`.

#### `GET /default-configurations/sensors/{configurationId}`

**Required parameters:** `configurationId` (integer, in path)

## 3. Developer Tips

**Secrets are returned masked, and this breaks the obvious edit pattern.** Any secret-bearing field comes
back as the literal string `"********"` when set. The real value is never returned by the API. Affected
fields include `passphraseOrPsk`, `password`, `preSharedKey`, `privateKeyPassword`,
`innerPrivateKeyPassword`, and `challengePassword`.

Combined with `PUT` being a full replace, the natural read-modify-write flow silently corrupts the key:

```python
# WRONG — this sets the passphrase to the literal string "********"
key = get_network_key(token, key_id)
key["name"] = "New name"
update_network_key(token, key_id, key)
```

```python
# RIGHT — re-supply real secret values, or don't PUT at all
key = get_network_key(token, key_id)
key["name"] = "New name"
key["passphraseOrPsk"] = prompt_for_passphrase()   # never reuse "********"
update_network_key(token, key_id, key)
```

If you only need to rename a key and don't have the passphrase to hand, you cannot do it safely through
`PUT` — you'd write the mask as the new secret.

**Ids are integers here.** `targetId`, `networkKeyId`, and `configurationId` are all numeric, as are the
`id` fields inside the objects. Don't validate them as UUIDs the way you would an `agentId` or a
`ruleId`.

**Query parameters.** The three list endpoints on this page return the standard
`{results, pagination}` envelope, and the repo-standard paging parameters are the ones to reach for:

| Parameter | Type | Description |
|-----------|------|-------------|
| `organization` | string | Defaults to the organization on your token |
| `page` | integer | **First page is 1**, not 0 |
| `perPage` | integer | Records per page |
| `sortField` | string | Field to sort on |
| `order` | string | `asc` or `desc` |

> **Caveat worth knowing:** the OpenAPI specification does not currently declare any query parameters
> for `GET /targets/sensors`, `GET /network-keys/sensors`, or `GET /default-configurations/sensors`, even
> though all three return a `pagination` object. Unrecognised parameters are ignored rather than
> rejected, so if paging appears to have no effect, check `pagination.page` in the response before
> assuming your loop is advancing.

**Deletes are reference-checked, not cascading.** A target still used by a test profile won't delete, and
a network key still bound to a wireless network or sensor returns `409`. This is a safety feature — treat
the failure as "something still depends on this" and go detach it, rather than retrying.

**Order of operations when setting up a new sensor deployment:**

1. Create the targets the sensors should test against (`POST /targets/sensors`).
2. Create the network keys for the SSIDs they'll join (`POST /network-keys/sensors`), starting from
   `GET /network-keys/sensors/templates` for captive portals.
3. Read the available bundles (`GET /default-configurations/sensors`) and reference the right
   `defaultConfigurationId` from the Service Area.

**Confirming destructive calls in a script.** Since `DELETE` and `PUT` here change live monitoring
configuration, prompt before sending:

```python
choice = input(f"Delete target {target_id}? Type 'yes' to confirm: ").strip().lower()
if choice != "yes":
    logging.info("Aborted; nothing was deleted.")
    return
```

## 4. Troubleshooting & FAQs

**Q: I renamed a network key and now sensors can't associate to that SSID.**

A: The `PUT` almost certainly wrote `"********"` as the passphrase. Secrets are returned masked, `PUT` is
a full replace, so echoing the fetched object back sets the mask as the literal secret. Re-`PUT` the key
with the real passphrase to fix it.

**Q: `DELETE /network-keys/sensors/{id}` returns `409`.**

A: The key is still bound to a wireless network or a sensor. Remove those bindings first — the API will
not unbind on your behalf.

**Q: My `DELETE` of a target failed.**

A: A test profile still references it. Detach the target from the profile, then delete.

**Q: I `PUT` a `SONAR` target with only `dnsName` and its IP address vanished.**

A: That's the documented behaviour — `dnsName`, `ipV4Address`, and `ipV6Address` fully replace their
previous values, and omitting one clears it. `GET` the target first and resend every address field you
want to keep.

**Q: I get a `400` creating a target and I did set a name and type.**

A: The address requirement is per-type. `WEB_SERVER` and `IPERF3_SERVER` need `dnsName` specifically;
`SONAR` and `PING_ENDPOINT` need at least one of `dnsName`, `ipV4Address`, or `ipV6Address`. An IPv4
address alone is not sufficient for a `WEB_SERVER`.

**Q: Can I change a target from `PING_ENDPOINT` to `SONAR`?**

A: No. `targetType` is fixed at creation and isn't part of the `PUT` body. Create a new target and
repoint the test profile.

**Q: `tcpPort` on my `WEB_SERVER` target is ignored.**

A: Correct — `tcpPort` only applies to `SONAR` (default `80`) and `IPERF3_SERVER` (default `5201`). For
`WEB_SERVER` and `PING_ENDPOINT` it's ignored. Encode a non-standard web port in the `dnsName` URL.

**Q: Can I create or edit a default configuration through this API?**

A: No, these two endpoints are read-only. They exist so you can discover a valid
`defaultConfigurationId` to reference from a Service Area or Organization.

**Q: Why is `passphraseOrPsk` missing entirely on my `WPA3_OWE` key?**

A: OWE doesn't use a shared secret, so the field is absent rather than masked. That's expected.
