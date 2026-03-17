---
name: "bakufu-global-exclusions"
version: "1.0.0"
description: "The Global Exclusions section defines paths and operations for managing which VMs will be excluded from processing, even if they are included in jobs. In this version, you can use these operations for VMware vSphere, VMware Cloud Director, and Microsoft Hyper-V VMs."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Global Exclusions

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Global Exclusions section defines paths and operations for managing which VMs will be excluded from processing, even if they are included in jobs. In this version, you can use these operations for VMware vSphere, VMware Cloud Director, and Microsoft Hyper-V VMs.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Global Exclusions"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
