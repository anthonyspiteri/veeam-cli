---
name: "bakufu-deployment"
version: "1.0.0"
description: "The Deployment section defines paths and operations for generating and downloading a deployment kit that is used for adding Windows machines as managed servers."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Deployment

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Deployment section defines paths and operations for generating and downloading a deployment kit that is used for adding Windows machines as managed servers.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Deployment"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
