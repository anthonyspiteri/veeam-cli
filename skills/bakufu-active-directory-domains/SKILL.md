---
name: "bakufu-active-directory-domains"
version: "1.0.0"
description: "The Active Directory Domains section defines paths and operations for managing Active Directory domains."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Active Directory Domains

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Active Directory Domains section defines paths and operations for managing Active Directory domains.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Active Directory Domains"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
