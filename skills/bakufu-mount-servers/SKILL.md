---
name: "bakufu-mount-servers"
version: "1.0.0"
description: "The Mount Servers section defines paths and operations for managing mount servers in your backup infrastructure. Mount servers are used in advanced restore operations (file restore, application item restore and Instant Recovery)."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Mount Servers

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Mount Servers section defines paths and operations for managing mount servers in your backup infrastructure. Mount servers are used in advanced restore operations (file restore, application item restore and Instant Recovery).

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Mount Servers"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
