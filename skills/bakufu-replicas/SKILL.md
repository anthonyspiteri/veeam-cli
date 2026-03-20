---
name: "bakufu-replicas"
version: "1.0.0"
description: "The Replicas section defines paths and operations for managing snapshot replicas."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Replicas

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Replicas section defines paths and operations for managing snapshot replicas.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Replicas"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
