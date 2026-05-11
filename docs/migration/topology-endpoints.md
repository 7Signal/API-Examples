# Migration Notes: Topology Endpoints

Gateway API Topologies endpoints have been deprecated and will be removed in a future release.

## Deprecated Endpoints

- `/topologies/agents/locations`
- `/topologies/agents/locations/{locationId}`
- `/topologies/sensors/locations`
- `/topologies/sensors/locations/{locationId}`
- `/topologies/sensors/serviceAreas`
- `/topologies/sensors/serviceAreas/{serviceAreaId}`
- `/topologies/sensors/accessPoints`
- `/topologies/sensors/accessPoints/{accessPointId}`

The inputs parameters and output structure for these API calls should be very similar to the new endpoints, but exact parity cannot be guaranteed. If fields are missing from the new endpoints, open a ticket and the team can evaluate including that property.

The new format can be found in the [OpenAPI Spec / Swagger UI](https://api-v2.7signal.com/swagger-ui/index.html).

## Endpoint Mapping

| **Deprecated** | **New** |
| --- | --- |
| `/topologies/agents/locations` | `/locations/agents` |
| `/topologies/agents/locations/{locationId}` | `/locations/agents/{locationId}` |
| `/topologies/sensors/locations` | `/locations/sensors` |
| `/topologies/sensors/locations/{locationId}` | `/locations/sensors/{locationId}` |
| `/topologies/sensors/serviceAreas` | `/service-areas/sensors` |
| `/topologies/sensors/serviceAreas/{serviceAreaId}` | `/service-areas/sensors/{serviceAreaId}` |
| `/topologies/sensors/accessPoints` | `/access-points/sensors` |
| `/topologies/sensors/accessPoints/{accessPointId}` | `/access-points/sensors/{accessPointId}` |
