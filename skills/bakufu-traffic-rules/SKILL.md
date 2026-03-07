---
name: "bakufu-traffic-rules"
version: "1.0.0"
description: "The Traffic Rules section defines paths and operations for retrieving and editing information about network traffic rules that are configured on the backup server."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Traffic Rules

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Traffic Rules section defines paths and operations for retrieving and editing information about network traffic rules that are configured on the backup server.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Traffic Rules"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
