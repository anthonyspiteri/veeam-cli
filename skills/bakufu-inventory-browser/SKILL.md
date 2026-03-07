---
name: "bakufu-inventory-browser"
version: "1.0.0"
description: "The Inventory Browser section defines paths and operations that allow you to&#58; Retrieve virtualization servers and their virtual infrastructure objects (data centers, clusters, hosts, resource pools, vApps, VMs and so on). In this version, you can browse VMware vSphere, VMware Cloud Director and Microsoft Hyper-V objects. Manage computers, cloud machines, clusters and Active Directory objects with protection groups. Manage unstructured data sources. Manage Microsoft Entra ID tenants."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Inventory Browser

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Inventory Browser section defines paths and operations that allow you to&#58; Retrieve virtualization servers and their virtual infrastructure objects (data centers, clusters, hosts, resource pools, vApps, VMs and so on). In this version, you can browse VMware vSphere, VMware Cloud Director and Microsoft Hyper-V objects. Manage computers, cloud machines, clusters and Active Directory objects with protection groups. Manage unstructured data sources. Manage Microsoft Entra ID tenants.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Inventory Browser"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
