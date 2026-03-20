---
name: "bakufu-backups"
version: "1.0.0"
description: "The Backups section defines paths and operations for managing backups that are created on or imported to the backup server."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Backups

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Backups section defines paths and operations for managing backups that are created on or imported to the backup server.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Backups"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
