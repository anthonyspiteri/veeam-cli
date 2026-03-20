---
name: "bakufu-data-integration-api"
version: "1.0.0"
description: "The Data Integration API section defines paths and operations for publishing disks from backups and snapshot replicas."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Data Integration Api

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Data Integration API section defines paths and operations for publishing disks from backups and snapshot replicas.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Data Integration Api"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
