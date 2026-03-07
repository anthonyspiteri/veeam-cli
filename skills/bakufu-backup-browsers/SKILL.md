---
name: "bakufu-backup-browsers"
version: "1.0.0"
description: "The Backup Browser section defines paths and operations that allow you to&#58; Browse the file system, compare files and folders, and perform file restore. Browse Microsoft Entra ID tenant backups, compare Microsoft Entra ID items, and restore entire items or their properties. Browse the Microsoft Entra ID log files, compare files and folders, and restore Microsoft Entra ID logs."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Backup Browsers

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Backup Browser section defines paths and operations that allow you to&#58; Browse the file system, compare files and folders, and perform file restore. Browse Microsoft Entra ID tenant backups, compare Microsoft Entra ID items, and restore entire items or their properties. Browse the Microsoft Entra ID log files, compare files and folders, and restore Microsoft Entra ID logs.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Backup Browsers"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
