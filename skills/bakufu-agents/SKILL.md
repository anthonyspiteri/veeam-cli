---
name: "bakufu-agents"
version: "1.0.0"
description: "The Agents section defines paths and operations for working with protection groups, obtaining protected computers, managing Veeam Agent and other Veeam components on the computers and handling recovery tokens used for bare metal recovery."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Agents

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Agents section defines paths and operations for working with protection groups, obtaining protected computers, managing Veeam Agent and other Veeam components on the computers and handling recovery tokens used for bare metal recovery.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Agents"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
