---
name: "bakufu-restore"
version: "1.0.0"
description: "The Restore section defines paths and operations for performing restore. NOTE In this version, the REST API supports the following recovery operations: Instant Recovery of a VMware vSphere VM to VMware vSphere Instant Recovery of a Microsoft Hyper-V VM to Microsoft Hyper-V Instant Recovery of Windows and Linux machines to Azure Instant File Share Recovery to the original or another location Entire VM restore of a VMware vSphere VM to VMware vSphere Entire VM restore of a Microsoft Hyper-V VM to Microsoft Hyper-V Entire VM restore of a VMware Cloud Director VM to VMware Cloud Director Restore of an entire file share, bucket or container to the original or another location Restore of disks that will be registered as First Class Disks (FCD) — a type of virtual disks that can be managed independent of any VM File restore from a backup or replica of a Microsoft Windows or Linux machine File restore from an unstructured data backup Microsoft Entra item restore Microsoft Entra audit log restore"
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Restore

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Restore section defines paths and operations for performing restore. NOTE In this version, the REST API supports the following recovery operations: Instant Recovery of a VMware vSphere VM to VMware vSphere Instant Recovery of a Microsoft Hyper-V VM to Microsoft Hyper-V Instant Recovery of Windows and Linux machines to Azure Instant File Share Recovery to the original or another location Entire VM restore of a VMware vSphere VM to VMware vSphere Entire VM restore of a Microsoft Hyper-V VM to Microsoft Hyper-V Entire VM restore of a VMware Cloud Director VM to VMware Cloud Director Restore of an entire file share, bucket or container to the original or another location Restore of disks that will be registered as First Class Disks (FCD) — a type of virtual disks that can be managed independent of any VM File restore from a backup or replica of a Microsoft Windows or Linux machine File restore from an unstructured data backup Microsoft Entra item restore Microsoft Entra audit log restore

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Restore"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
