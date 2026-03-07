---
name: "bakufu-service"
version: "1.0.0"
description: "The Service section defines paths and operations for retrieving information about the backup server where the REST API service is running."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Service

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Service section defines paths and operations for retrieving information about the backup server where the REST API service is running.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Service"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
