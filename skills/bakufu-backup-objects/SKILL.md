---
name: "bakufu-backup-objects"
version: "1.0.0"
description: "The Backup Objects section defines paths and operations for managing backup objects — VMs and vApps that are included in backups created by the backup server. Types of backup objects differ depending on the backup job platform: Backups of VMware vSphere jobs contain VMs only. Backups of VMware Cloud Director jobs contain VMs and vApps."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Backup Objects

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Backup Objects section defines paths and operations for managing backup objects — VMs and vApps that are included in backups created by the backup server. Types of backup objects differ depending on the backup job platform: Backups of VMware vSphere jobs contain VMs only. Backups of VMware Cloud Director jobs contain VMs and vApps.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Backup Objects"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
