---
name: "recipe-sobr-tier-health"
version: "1.0.0"
description: "Review SOBR extent states, capacity tier offload, and maintenance mode."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-repositories"
        - "bakufu-repo-capacity"
        - "bakufu-sobr-list"
---
# Recipe Sobr Tier Health

PREREQUISITE: Load the following utility skills first: `bakufu-repositories`, `bakufu-repo-capacity`, `bakufu-sobr-list`

Review SOBR extent states, capacity tier offload, and maintenance mode.

## Relevant Commands

- `bakufu run Repositories GetAllScaleOutRepositories --pretty`
- `bakufu workflows capacityReport`
- `bakufu run Repositories GetAllRepositoriesStates --pretty`

## Instructions
- List all SOBRs and their extent configurations first.
- Check for extents in maintenance or sealed mode that may block offload.
- Correlate performance tier capacity with capacity tier offload schedules.
- Flag any SOBR with no capacity tier configured as a gap.

## Tips
- Include SOBR tier health in weekly storage administration reviews.
- Track offload progress over time to detect stalled transfers.
