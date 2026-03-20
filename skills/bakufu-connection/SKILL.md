---
name: "bakufu-connection"
version: "1.0.0"
description: "The Connection section defines a path and operation for retrieving a TLS certificate or SSH fingerprint used to establish a secure connection between the backup server and the specified server."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Connection

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Connection section defines a path and operation for retrieving a TLS certificate or SSH fingerprint used to establish a secure connection between the backup server and the specified server.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Connection"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
