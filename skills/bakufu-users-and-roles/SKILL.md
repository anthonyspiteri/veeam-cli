---
name: "bakufu-users-and-roles"
version: "1.0.0"
description: "The Users and Roles section defines paths and operations for managing Veeam Backup & Replication users, groups and assigned roles."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Users And Roles

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Users and Roles section defines paths and operations for managing Veeam Backup & Replication users, groups and assigned roles.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Users And Roles"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
