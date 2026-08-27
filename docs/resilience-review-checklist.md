# Resilience Review Checklist

## Business and objectives

- [ ] Business impact is expressed in customer and operational terms.
- [ ] Availability target, RTO, and RPO are approved by accountable owners.
- [ ] Degraded modes and manual business workarounds are documented.
- [ ] Recovery priorities are ordered across services and dependencies.

## Architecture

- [ ] Critical paths include edge, identity, secrets, data, messaging, observability, and third parties.
- [ ] Failure domains are independent enough to survive the intended event.
- [ ] Multi-region is paired with routing, data, deployment, and capacity strategies.
- [ ] Required and optional dependencies are modeled explicitly.
- [ ] Retry, timeout, circuit-breaker, and backpressure behavior is defined.

## Data

- [ ] Replication and backup protect against different failure modes.
- [ ] Restore tests prove integrity, encryption access, and measured RPO/RTO.
- [ ] Regional failover behavior accounts for consistency and conflict resolution.
- [ ] Destructive logical failures and credential compromise are included.

## Operations

- [ ] Health probes validate customer-serving behavior, not just process liveness.
- [ ] Alerts map to service objectives and named responders.
- [ ] Runbooks include triggers, authority, commands, validation, rollback, and communication.
- [ ] The surviving region has load-tested peak capacity plus headroom.
- [ ] Game days capture evidence, decisions, surprises, and follow-up owners.

## Change safety

- [ ] Deployments are independently controllable by failure domain.
- [ ] Configuration and secrets can roll back safely.
- [ ] Infrastructure changes use preview/what-if and policy checks.
- [ ] Architecture specifications and generated reports are reviewed in pull requests.
