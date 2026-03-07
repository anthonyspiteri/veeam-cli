---
name: "bakufu-security"
version: "1.0.0"
description: "The Security section defines paths and operations for managing Security & Compliance Analyzer and getting four-eyes authorization events."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Security

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Security section defines paths and operations for managing Security & Compliance Analyzer and getting four-eyes authorization events.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Security"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
