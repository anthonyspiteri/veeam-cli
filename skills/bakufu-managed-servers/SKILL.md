---
name: "bakufu-managed-servers"
version: "1.0.0"
description: "The Managed Servers section defines paths and operations for managing servers. NOTE In this version, the REST API supports the following server types&#58; *VMware vSphere*, *Hyper-V*, *Linux* and *Windows*."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Managed Servers

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Managed Servers section defines paths and operations for managing servers. NOTE In this version, the REST API supports the following server types&#58; *VMware vSphere*, *Hyper-V*, *Linux* and *Windows*.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Managed Servers"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
