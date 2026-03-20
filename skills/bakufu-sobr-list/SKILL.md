---
name: "bakufu-sobr-list"
version: "1.0.0"
description: "List scale-out backup repositories with tier details."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-repositories"
---
# Bakufu Sobr List

PREREQUISITE: Load the following utility skills first: `bakufu-repositories`

List scale-out backup repositories with tier details.

## Relevant Commands

- `bakufu run Repositories GetAllScaleOutRepositories`

## Instructions
- Use SOBR listing to understand performance and capacity tier assignments.
- Check extent states for maintenance or sealed mode entries.
- Correlate SOBR configuration with capacity report data.

## Tips
- Document SOBR tier topology changes in infrastructure runbooks.
- Monitor extent count growth against licensing limits.
