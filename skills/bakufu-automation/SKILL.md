---
name: "bakufu-automation"
version: "1.0.0"
description: "The Automation section defines paths and operations for granular import and export of objects available in the REST API. It can be useful, for example, if you set up the backup infrastructure using JSON specification or migrate the infrastructure to another backup server. For details, see [Mass Deployment](https://helpcenter.veeam.com/references/vbr/13/rest/1.3-rev1/tag/SectionHowTo#section/Mass-Deployment)."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Automation

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Automation section defines paths and operations for granular import and export of objects available in the REST API. It can be useful, for example, if you set up the backup infrastructure using JSON specification or migrate the infrastructure to another backup server. For details, see [Mass Deployment](https://helpcenter.veeam.com/references/vbr/13/rest/1.3-rev1/tag/SectionHowTo#section/Mass-Deployment).

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Automation"`
- `bakufu run <Tag> <OperationId> --params '{}'`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
