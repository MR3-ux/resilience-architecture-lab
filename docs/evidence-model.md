# Resilience Evidence Model

Resilience is not a product feature; it is a claim supported by evidence.

| Claim | Weak evidence | Stronger evidence |
|---|---|---|
| A region can fail without outage | Two regions on a diagram | Successful controlled failover under production-like load |
| RTO is 30 minutes | A number in a document | Timestamped game-day record showing detection, decision, and restoration |
| RPO is 5 minutes | Backup schedule | Successful restore with measured recovery point and integrity checks |
| Health probes protect users | HTTP 200 on `/health` | Dependency-aware probe plus observed traffic removal and recovery |
| Surviving capacity is sufficient | Autoscale enabled | Load test at peak plus headroom with one region removed |
| Alerts are actionable | Alert rules exist | On-call exercise showing signal, routing, diagnosis, and runbook execution |

## Evidence lifecycle

1. **Declare** the objective and architecture assumption.
2. **Automate** the control where appropriate.
3. **Exercise** the failure under controlled conditions.
4. **Measure** customer effect, restore time, and data loss.
5. **Review** the result with owners and risk stakeholders.
6. **Expire** stale evidence when architecture, traffic, or dependencies change.

The lab currently covers declaration and deterministic review. The roadmap adds signed exercise evidence and evidence freshness.
