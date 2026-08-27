# ADR-0002: Evaluate service restoration and data loss separately

- **Status:** Accepted
- **Date:** 2026-08-27

## Context

A service can return within its recovery time objective while still losing more data than its recovery point objective permits. Combining these outcomes into one pass/fail hides material risk.

## Decision

Every scenario reports:

- Customer-visible system status.
- Estimated service-restoration minutes and RTO result.
- Estimated data-loss minutes and RPO result.

Replication RPO is used when a stateful component survives through regional replication. Backup RPO is used when the component itself is unavailable and recovery requires a backup path.

## Consequences

The reference design can score strongly on static controls yet still fail the RPO in a total database-service outage. This is intentional: scenario evidence is allowed to challenge the design score.
