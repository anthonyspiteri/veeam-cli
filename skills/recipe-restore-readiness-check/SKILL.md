---
name: "recipe-restore-readiness-check"
version: "1.0.0"
description: "Validate restore paths, mount servers, and key dependencies."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-restore"
        - "bakufu-restore-points"
        - "bakufu-mount-servers"
        - "bakufu-repositories"
---
# Recipe Restore Readiness Check

PREREQUISITE: Load the following utility skills first: `bakufu-restore`, `bakufu-restore-points`, `bakufu-mount-servers`, `bakufu-repositories`

Validate restore paths, mount servers, and key dependencies.

## Relevant Commands

- `bakufu run RestorePoints GetAllRestorePoints --pretty`
- `bakufu run MountServers GetAllMountServers --pretty`
- `bakufu run Repositories GetAllRepositories --pretty`
- `bakufu run Restore GetRestoreSummary --pretty`

## Instructions
- Verify restore points exist for critical workloads and are within SLA age.
- Confirm mount servers are reachable and have sufficient temporary storage.
- Check repository health and connectivity for each restore target.
- Document any missing restore paths or unavailable dependencies as blockers.

## Tips
- Run readiness checks before DR test windows, not during.
- Keep a known-good restore point inventory for rapid incident response.
