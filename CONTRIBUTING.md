# Contributing

Architecture challenges are welcome when they are specific, testable, and respectful.

## Development

```bash
git clone https://github.com/MR3-ux/resilience-architecture-lab.git
cd resilience-architecture-lab
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The runtime intentionally has no third-party dependencies. Keep the core engine deterministic and offline.

## Change expectations

- Add tests for new failure or dependency semantics.
- Regenerate `reports/demo/` when output behavior changes.
- Record architectural decisions that change trust, safety, or modeling boundaries.
- State assumptions rather than disguising them as facts.
- Avoid cloud credentials, real tenant identifiers, production output, or customer data.

## Commit style

Use a short imperative subject, for example:

```text
model optional dependency degradation
add database restore runbook
explain capacity assumption in reference design
```
