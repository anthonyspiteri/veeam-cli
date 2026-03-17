---
name: "recipe-repository-health-review"
version: "1.0.0"
description: "Review repository connectivity, component versions, and capacity status."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-repositories"
        - "bakufu-repo-capacity"
---
# Recipe Repository Health Review

PREREQUISITE: Load the following utility skills first: `bakufu-repositories`, `bakufu-repo-capacity`

Review repository connectivity, component versions, and capacity status.

## Relevant Commands

- `bakufu run Repositories GetAllRepositories --pretty`
- `bakufu workflows capacityReport`

## Instructions
- List all repositories and verify online/offline status.
- Check repository component versions and flag any that are out of date.
- Review capacity utilization and free space against defined thresholds.
- Identify repositories approaching capacity limits for proactive expansion.

## Tips
- Include repository health in weekly infrastructure review alongside proxy status.
- Track capacity trends over time to predict when expansion is needed.
- Correlate repository connectivity issues with managed server health.
