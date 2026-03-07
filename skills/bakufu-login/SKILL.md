---
name: "bakufu-login"
version: "1.0.0"
description: "The authorization process involves obtaining an access token and a refresh token. For details on the authorization process and security settings, see [Authorization and Security](https://helpcenter.veeam.com/references/vbr/13/rest/1.3-rev1/tag/SectionOverview#section/Authorization-and-Security)."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Login

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The authorization process involves obtaining an access token and a refresh token. For details on the authorization process and security settings, see [Authorization and Security](https://helpcenter.veeam.com/references/vbr/13/rest/1.3-rev1/tag/SectionOverview#section/Authorization-and-Security).

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Login"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
