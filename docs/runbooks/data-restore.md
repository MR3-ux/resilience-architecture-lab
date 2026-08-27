# Runbook: Stateful Service Restore

## Trigger

- Logical corruption, destructive change, or full service loss requires recovery from a protected copy.

## Preconditions

- Named recovery authority and business data owner.
- Tested access to encrypted backups independent of the failed service path.
- Known clean recovery point and integrity-validation procedure.

## Response

1. Stop or isolate writes that could worsen corruption.
2. Preserve evidence and determine the failure scope.
3. Select a recovery point based on integrity first, then data-loss impact.
4. Restore into an isolated environment.
5. Validate schema, record counts, checksums, access controls, and representative transactions.
6. Reconcile unavoidable data loss with source systems and business owners.
7. Obtain explicit approval before redirecting production traffic.
8. Monitor correctness and performance after cutover.

## Measures

- Detection time.
- Restore start and completion time.
- Recovery point timestamp.
- Actual RTO and RPO.
- Integrity defects and reconciliation volume.
