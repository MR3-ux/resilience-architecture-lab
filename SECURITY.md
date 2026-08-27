# Security Policy

## Supported version

Security fixes are applied to the latest version on the `main` branch.

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Use GitHub's private vulnerability reporting feature when enabled, or contact the repository owner privately.

Include the affected version, reproduction steps, impact, and any suggested mitigation. Do not include real cloud credentials, tenant IDs, subscription IDs, access tokens, customer data, or production diagnostic output.

## Security design

- The runtime is offline and standard-library-only.
- Architecture inputs are read from local JSON files.
- The engine does not execute content from the specification.
- The engine does not invoke Azure CLI or access cloud accounts.
- Generated reports may expose architecture details and should be reviewed before publication.
