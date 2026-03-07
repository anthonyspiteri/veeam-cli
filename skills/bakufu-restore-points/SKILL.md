---
name: "bakufu-restore-points"
version: "1.0.0"
description: "The Restore Points section defines paths and operations for retrieving restore points created on the backup server and backed up disks from the restore points."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Restore Points

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Restore Points section defines paths and operations for retrieving restore points created on the backup server and backed up disks from the restore points.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Restore Points"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
