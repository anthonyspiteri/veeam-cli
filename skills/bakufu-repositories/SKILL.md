---
name: "bakufu-repositories"
version: "1.0.0"
description: "The Repositories section defines paths and operations for managing backup repositories. NOTE In this version, the REST API supports the following storage types&#58; direct attached storages (Microsoft Windows and Linux servers), network attached storages (SMB and NFS shares), object storages and Veeam Data Cloud Vault repositories. For details on how to add an object storage repository, see [Object Storage Repositories](https://helpcenter.veeam.com/references/vbr/13/rest/1.3-rev1/tag/SectionHowTo#section/Object-Storage-Repositories)."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Repositories

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Repositories section defines paths and operations for managing backup repositories. NOTE In this version, the REST API supports the following storage types&#58; direct attached storages (Microsoft Windows and Linux servers), network attached storages (SMB and NFS shares), object storages and Veeam Data Cloud Vault repositories. For details on how to add an object storage repository, see [Object Storage Repositories](https://helpcenter.veeam.com/references/vbr/13/rest/1.3-rev1/tag/SectionHowTo#section/Object-Storage-Repositories).

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Repositories"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
