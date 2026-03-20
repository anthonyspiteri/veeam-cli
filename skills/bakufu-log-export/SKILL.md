---
name: "bakufu-log-export"
version: "1.0.0"
description: "The Log Export section defines paths and operations for exporting the backup server logs."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Log Export

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Log Export section defines paths and operations for exporting the backup server logs.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Log Export"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
