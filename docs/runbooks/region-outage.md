# Runbook: Regional Outage

## Trigger

- Regional platform health event, or
- Dependency-aware probes fail in one region while the peer region remains healthy.

## Safety rules

- Do not force traffic to a region until health and capacity are confirmed.
- Do not disable probes merely to make dashboards green.
- Preserve timelines, alerts, configuration changes, and decision evidence.

## Response

1. Declare an incident and assign incident commander, operations lead, and communications lead.
2. Confirm customer impact from edge telemetry and synthetic transactions.
3. Separate regional failure from application deployment or shared-dependency failure.
4. Confirm the surviving region's application, identity, secrets, and data health.
5. Verify capacity and autoscale headroom before increasing traffic.
6. Observe automatic traffic removal; intervene manually only under documented authority.
7. Validate transactions end to end, including reads, writes, authentication, and downstream events.
8. Record detection time, failover time, error rate, latency, and data consistency evidence.

## Recovery

1. Do not rebalance immediately when the region returns.
2. Validate data convergence, configuration, deployed version, secrets, and background processing.
3. Reintroduce traffic gradually with abort thresholds.
4. Close only after customer metrics and queued work return to normal.

## Evidence to retain

- Incident timeline and decision log.
- Traffic distribution and capacity graphs.
- Synthetic transaction results.
- Measured RTO/RPO and any violated objective.
- Follow-up actions with owners and due dates.
