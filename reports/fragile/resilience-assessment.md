# Resilience Assessment: Single-Region Checkout

> Generated deterministically by Resilience Architecture Lab v0.1.0 from the version-controlled model.

## Executive summary

**Resilience score:** 19/100 (fragile)

An intentionally fragile architecture used to demonstrate design findings and failed objectives.

**Business impact:** Checkout downtime stops revenue and may lose accepted orders.

**Objectives:** 99.9% availability; RTO 15 minutes; RPO 5 minutes.

## Scorecard

| Dimension | Score | Maximum |
|---|---:|---:|
| Objectives and ownership | 15 | 15 |
| Failure-domain redundancy | 0 | 20 |
| Detection and failover | 0 | 20 |
| Data protection | 0 | 20 |
| Observability | 0 | 15 |
| Dependency resilience | 4 | 10 |
| **Total** | **19** | **100** |

## Failure scenarios

| Scenario | Result | Restore | Data loss | RTO | RPO |
|---|---|---:|---:|---|---|
| East US regional outage | OUTAGE | 240 min | 1440 min | FAIL | FAIL |
| Database outage | OUTAGE | 120 min | 1440 min | FAIL | FAIL |

## Findings

### 1. [CRITICAL] Critical component is a single point of failure

- **Category:** redundancy
- **Component:** `web`
- **Evidence:** Single Web Server has one replica in eastus.
- **Recommendation:** Add failure-domain redundancy and document the traffic or workload failover path.

### 2. [HIGH] No health signal drives failover

- **Category:** failover
- **Component:** `web`
- **Evidence:** The component is critical but health_check is false.
- **Recommendation:** Define an end-to-end health probe that validates dependencies and customer-serving behavior.

### 3. [MEDIUM] Critical telemetry coverage is incomplete

- **Category:** observability
- **Component:** `web`
- **Evidence:** Missing signals: alerts, metrics.
- **Recommendation:** Instrument golden signals, structured logs, and actionable alerts tied to the service objectives.

### 4. [HIGH] Critical path depends on a single-instance service

- **Category:** dependency
- **Component:** `web`
- **Evidence:** Single Web Server requires Single Database, which has no failure-domain redundancy.
- **Recommendation:** Remove the dependency SPOF, add a degraded mode, or make the dependency redundant.

### 5. [HIGH] Critical component is a single point of failure

- **Category:** redundancy
- **Component:** `database`
- **Evidence:** Single Database has one replica in eastus.
- **Recommendation:** Add failure-domain redundancy and document the traffic or workload failover path.

### 6. [HIGH] No health signal drives failover

- **Category:** failover
- **Component:** `database`
- **Evidence:** The component is critical but health_check is false.
- **Recommendation:** Define an end-to-end health probe that validates dependencies and customer-serving behavior.

### 7. [HIGH] Data protection does not meet the system RPO

- **Category:** data-protection
- **Component:** `database`
- **Evidence:** Best documented RPO is 1440 minutes; target is 5.
- **Recommendation:** Improve replication or backup frequency and prove recovery with a restore test.

### 8. [MEDIUM] Critical telemetry coverage is incomplete

- **Category:** observability
- **Component:** `database`
- **Evidence:** Missing signals: alerts, metrics.
- **Recommendation:** Instrument golden signals, structured logs, and actionable alerts tied to the service objectives.

## Scenario evidence

### East US regional outage

| Component | State | Reason |
|---|---|---|
| `web` | unavailable | Region 'eastus' contains all available instances and no viable automated failover remains. |
| `database` | unavailable | Region 'eastus' contains all available instances and no viable automated failover remains. |

### Database outage

| Component | State | Reason |
|---|---|---|
| `web` | unavailable | Required dependency unavailable: database. |
| `database` | unavailable | Direct outage of component 'database'. |

## Assumptions and limits

- This example is intentionally weak and must not be copied into production.
- Results are deterministic design-review evidence, not a substitute for production telemetry or controlled chaos experiments.
- Recovery estimates are only as credible as the runbooks, automation, capacity tests, and restore exercises behind the input values.
