# 7SIGNAL API Documentation

This directory contains the 7SIGNAL API reference documentation. The base URL for all API endpoints is `https://api-v2.7signal.com`.

## Contents

| # | Document | Description |
|---|----------|-------------|
| 1 | [Authentication](01-authentication.md) | How to obtain and use Bearer tokens via API Key & Secret |
| 2 | [Rate Limiting](02-rate-limiting.md) | Rate limit headers, token bucket behavior, and 429 handling |
| 3 | [User Management](03-user-management.md) | CRUD operations for users, roles, groups, and organizations |
| 4 | [API Keys](04-api-keys.md) | Creating and managing API keys for programmatic access |
| 5 | [Eyes (Agents)](05-eyes-agents.md) | Endpoints for listing, searching, and managing client agents |
| 6 | [Eyes (Sensors)](06-eyes-sensors.md) | Endpoints for listing and managing hardware WiFi sensors |
| 7 | [Topologies, Networks, Access Points](07-topologies-networks-access-points.md) | Location hierarchy, network groups, and access point management |
| 8 | [Packet Capture](08-packet-capture.md) | On-demand 802.11 packet capture tests on sensors |
| 9 | [Time Series](09-time-series.md) | Retrieving numeric, discrete, histogram, and summary time series data |
| 10 | [KPIs](10-kpis.md) | Key Performance Indicator endpoints for sensors and agents (see migration notes) |
| 11 | [Organizations, Groups, Roles](11-organizations-groups-roles.md) | Read-only endpoints for identity and access metadata |
| 12 | [Integration Configs](12-integration-configs.md) | Meraki Cloud API integration configuration and scheduling |
| 13 | [On-Demand Tests](13-on-demand-tests.md) | Ping, traceroute, HTTP/TCP/UDP throughput, speedtest, iPerf3, MOS, and web download tests |
| 14 | [Impact](14-impact.md) | Agent and location impact metrics (experience score, connectivity, coverage, congestion, interference, roaming) |
| 15 | [Scans](15-scans.md) | RF scan data collected by agents and sensors (detected APs, signal strength, channel, noise floor) |
| 16 | [Alerting](16-alerting.md) | Alert rules and the incidents they raise — thresholds, dimensions, notifications, resolution |
| 17 | [Eyeris Analysis](17-eyeris-analysis.md) | AI-generated analysis of an agent's experience, by polling or Server-Sent Events |
| 18 | [Agent Incidents](18-agent-incidents.md) | Platform-detected incidents where a share of the agent population degraded together |
| 19 | [Sensor Targets, Network Keys & Default Configurations](19-sensor-targets-and-network-keys.md) | What sensors test toward, the credentials they connect with, and the bundles tying them together |
| 20 | [Agent Service Areas](20-agent-service-areas.md) | Sub-divisions of a location, with bulk and single-record operations |
| 21 | [Sensor Clients & Change Events](21-sensor-clients-and-change-events.md) | Client devices sensors observed, and configuration changes on sensor-side elements |
| 22 | [Agent Audit & User Summaries](22-audit-and-user-summaries.md) | The agent audit trail, and user totals with recent-login counts |

## What's New

| Document | Description |
|----------|-------------|
| [What's New](WHATS-NEW.md) | Recently added endpoints, grouped by capability, with links to their reference pages and examples |

## Migration Notes

| Document | Description |
|----------|-------------|
| [Topology Endpoints](migration/topology-endpoints.md) | Deprecated `/topologies/*` endpoints and their replacements |
| [KPI Endpoints](migration/kpi-endpoints.md) | Deprecated `/kpis/*` endpoints and migration to Time Series |

## Quick Start

1. Obtain an API Key and Secret (see [API Keys](04-api-keys.md))
2. Authenticate to get a Bearer token (see [Authentication](01-authentication.md))
3. Include the token in all requests: `Authorization: Bearer <token>`
4. Tokens are valid for 24 hours — reuse them; don't request a new token per call

## Swagger / OpenAPI

Interactive API docs are available at:  
`https://api-v2.7signal.com/swagger-ui/index.html`
