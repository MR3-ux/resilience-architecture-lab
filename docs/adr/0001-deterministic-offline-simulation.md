# ADR-0001: Use deterministic offline simulation

- **Status:** Accepted
- **Date:** 2026-08-27

## Context

The project needs to teach and demonstrate failure reasoning without requiring an Azure subscription, credentials, production access, or cloud spend. It must also be safe to run in CI.

## Decision

Use a version-controlled architecture specification and a deterministic dependency-propagation engine. The runtime will use only the Python standard library and will not call cloud APIs.

## Consequences

### Positive

- Safe, repeatable, reviewable, and inexpensive.
- Results change only when the model or engine changes.
- Pull requests can show architecture and resilience-report diffs.
- Tests can cover failure semantics precisely.

### Negative

- Input values are assertions until supported by operational evidence.
- The model does not capture real latency, load, control-plane behavior, or emergent failure.
- It cannot replace chaos experiments, restore tests, or game days.

## Follow-up

Future integrations may import evidence from Azure, but offline assessment remains the default and cloud access must be explicitly enabled.
