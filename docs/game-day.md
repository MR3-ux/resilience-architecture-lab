# Game Day: Lose One Azure Region

## Objective

Demonstrate that the customer portal remains usable, the surviving region carries peak load, and data remains within the declared 5-minute RPO.

## Hypothesis

When one application region and its regional Key Vault become unavailable, Azure Front Door removes the failed origin within two minutes. The peer region handles full traffic while Cosmos DB preserves writes with no more than one minute of data exposure.

## Abort conditions

- Error rate exceeds the agreed threshold for more than five minutes.
- Surviving-region capacity exceeds the safe ceiling.
- Data integrity becomes uncertain.
- Incident commander cannot verify rollback authority.

## Exercise

1. Record baseline traffic, errors, latency, saturation, and replication health.
2. Confirm responders, communication channel, and rollback path.
3. Remove one region from service using the approved safe test mechanism.
4. Observe detection, routing, capacity, data, and customer journey results.
5. Run representative reads, writes, authentication, and background operations.
6. Restore the region and reintroduce traffic gradually.

## Review questions

- Did the failure look like the architecture model predicted?
- Which shared dependencies behaved differently?
- Did probes detect customer impact or only infrastructure state?
- Were RTO and RPO measured rather than inferred?
- What should change in the model, automation, runbook, or architecture?
