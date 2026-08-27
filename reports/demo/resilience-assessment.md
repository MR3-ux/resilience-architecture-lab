# Resilience Assessment: Atlas Customer Portal

> Generated deterministically by Resilience Architecture Lab v0.1.0 from the version-controlled model.

## Executive summary

**Resilience score:** 100/100 (production-minded)

An Azure active-active web platform designed to preserve customer access during regional and component failures.

**Business impact:** An outage blocks customer transactions and creates revenue, support, and contractual availability impact.

**Objectives:** 99.95% availability; RTO 30 minutes; RPO 5 minutes.

## Scorecard

| Dimension | Score | Maximum |
|---|---:|---:|
| Objectives and ownership | 15 | 15 |
| Failure-domain redundancy | 20 | 20 |
| Detection and failover | 20 | 20 |
| Data protection | 20 | 20 |
| Observability | 15 | 15 |
| Dependency resilience | 10 | 10 |
| **Total** | **100** | **100** |

## Failure scenarios

| Scenario | Result | Restore | Data loss | RTO | RPO |
|---|---|---:|---:|---|---|
| East US regional outage | DEGRADED | 2 min | 1 min | PASS | PASS |
| West US 2 regional outage | DEGRADED | 2 min | 1 min | PASS | PASS |
| Cosmos DB logical service outage | OUTAGE | 20 min | 15 min | PASS | FAIL |
| Identity provider outage | OUTAGE | 10 min | 0 min | PASS | PASS |
| Global edge component outage | OUTAGE | 5 min | 0 min | PASS | PASS |

## Findings

No static design gaps were detected by the current ruleset.

## Scenario evidence

### East US regional outage

| Component | State | Reason |
|---|---|---|
| `front-door` | degraded | One or more required dependencies are degraded or unavailable, but service can continue. |
| `app-east` | unavailable | Region 'eastus' contains all available instances and no viable automated failover remains. |
| `app-west` | degraded | One or more required dependencies are degraded or unavailable, but service can continue. |
| `cosmos` | degraded | Region 'eastus' is unavailable; automated failover to westus2 is expected in 2 minutes. |
| `key-vault-east` | unavailable | Region 'eastus' contains all available instances and no viable automated failover remains. |

### West US 2 regional outage

| Component | State | Reason |
|---|---|---|
| `front-door` | degraded | One or more required dependencies are degraded or unavailable, but service can continue. |
| `app-east` | degraded | One or more required dependencies are degraded or unavailable, but service can continue. |
| `app-west` | unavailable | Region 'westus2' contains all available instances and no viable automated failover remains. |
| `cosmos` | degraded | Region 'westus2' is unavailable; automated failover to eastus is expected in 2 minutes. |
| `key-vault-west` | unavailable | Region 'westus2' contains all available instances and no viable automated failover remains. |

### Cosmos DB logical service outage

| Component | State | Reason |
|---|---|---|
| `front-door` | unavailable | All alternative required dependencies are unavailable. |
| `app-east` | unavailable | Required dependency unavailable: cosmos. |
| `app-west` | unavailable | Required dependency unavailable: cosmos. |
| `cosmos` | unavailable | Direct outage of component 'cosmos'. |

### Identity provider outage

| Component | State | Reason |
|---|---|---|
| `front-door` | unavailable | All alternative required dependencies are unavailable. |
| `app-east` | unavailable | Required dependency unavailable: identity. |
| `app-west` | unavailable | Required dependency unavailable: identity. |
| `identity` | unavailable | Direct outage of component 'identity'. |

### Global edge component outage

| Component | State | Reason |
|---|---|---|
| `front-door` | unavailable | Direct outage of component 'front-door'. |

## Assumptions and limits

- Each application region has tested capacity to carry 100 percent of peak production traffic.
- Azure Front Door health probes validate a dependency-aware application health endpoint.
- Cosmos DB uses multi-region writes and continuous backup; restore exercises are performed quarterly.
- The values in this example are design assumptions for demonstration, not measured production evidence.
- Results are deterministic design-review evidence, not a substitute for production telemetry or controlled chaos experiments.
- Recovery estimates are only as credible as the runbooks, automation, capacity tests, and restore exercises behind the input values.
