---
name: "bakufu-managed-server-rescan"
version: "1.0.0"
description: "Rescan a managed server or all servers and return result state."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-managed-servers"
        - "bakufu-sessions"
---
# Bakufu Managed Server Rescan

PREREQUISITE: Load the following utility skills first: `bakufu-managed-servers`, `bakufu-sessions`

Rescan a managed server or all servers and return result state.

## Relevant Commands

- `bakufu run ManagedServers RescanManagedServer --params '{"id": "<server-id>"}' --pretty`
- `bakufu run ManagedServers RescanAllManagedServers --pretty`

## Instructions
- Trigger rescan after infrastructure changes (credentials, network, or component updates).
- Follow the rescan session to terminal state and capture any warnings.
- Use the all-server rescan for periodic infrastructure health checks.

## Tips
- Schedule rescans during low-activity periods to avoid contention.
- Capture rescan session IDs for component update tracking.
