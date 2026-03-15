---
name: "recipe-server-rescan"
version: "1.0.0"
description: "Rescan managed servers and validate component versions."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-managed-servers"
        - "bakufu-sessions"
        - "bakufu-managed-server-rescan"
---
# Recipe Server Rescan

PREREQUISITE: Load the following utility skills first: `bakufu-managed-servers`, `bakufu-sessions`, `bakufu-managed-server-rescan`

Rescan managed servers and validate component versions.

## Relevant Commands

- `bakufu run ManagedServers GetAllManagedServers --pretty`
- `bakufu run ManagedServers RescanManagedServer --params '{"id": "<server-id>"}' --pretty`
- `bakufu sessions show <session-id> --pretty`

## Instructions
- List managed servers and identify targets requiring rescan.
- Trigger rescan for specific servers or use the all-server rescan endpoint.
- Follow the rescan session and capture any component version mismatches.
- Flag servers with unavailable or error states for immediate investigation.

## Tips
- Run after Veeam version upgrades to detect component drift across servers.
- Document rescan outcomes in infrastructure change logs.
