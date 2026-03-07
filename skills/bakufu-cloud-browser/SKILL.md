---
name: "bakufu-cloud-browser"
version: "1.0.0"
description: "The Cloud Browser section defines paths and operations for retrieving information about cloud compute and storage resources. The Cloud Browser section helps you map a cloud folder with an object storage repository."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Cloud Browser

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Cloud Browser section defines paths and operations for retrieving information about cloud compute and storage resources. The Cloud Browser section helps you map a cloud folder with an object storage repository.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Cloud Browser"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
