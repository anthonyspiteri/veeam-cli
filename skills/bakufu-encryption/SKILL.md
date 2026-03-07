---
name: "bakufu-encryption"
version: "1.0.0"
description: "The Encryption section defines paths and operations for managing KMS servers and passwords that are used for data encryption."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Encryption

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Encryption section defines paths and operations for managing KMS servers and passwords that are used for data encryption.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Encryption"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
