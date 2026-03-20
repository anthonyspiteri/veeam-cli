---
name: "bakufu-services"
version: "1.0.0"
description: "The Services section defines a path and operation for retrieving information about associated backend services. You may need to connect to these services for integration with Veeam Backup & Replication."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Services

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Services section defines a path and operation for retrieving information about associated backend services. You may need to connect to these services for integration with Veeam Backup & Replication.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Services"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
