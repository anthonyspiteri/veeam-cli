---
name: "bakufu-tasks"
version: "1.0.0"
description: "The Tasks section defines paths and operations for managing tasks that are used to perform runtime operations (file restore and rescan of inventory objects)."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Tasks

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Tasks section defines paths and operations for managing tasks that are used to perform runtime operations (file restore and rescan of inventory objects).

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Tasks"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
