---
name: "bakufu-repo-capacity"
version: "1.0.0"
description: "Summarize repository capacity and free space."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-repositories"
---
# Bakufu Repo Capacity

PREREQUISITE: Load the following utility skills first: `bakufu-repositories`

Summarize repository capacity and free space.

## Relevant Commands

- `bakufu workflows capacityReport`
- `bakufu run Repositories GetAllRepositories`

## Instructions
- Assess free space and growth patterns before approving policy expansion.
- Highlight repositories near threshold with concrete remediation.
- Cross-check capacity anomalies against recent job/session behavior.

## Tips
- Include capacity snapshots in weekly operations reports.
- Treat sudden free-space drops as incident candidates.
