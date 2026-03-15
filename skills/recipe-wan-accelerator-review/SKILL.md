---
name: "recipe-wan-accelerator-review"
version: "1.0.0"
description: "List WAN accelerators and review cache configuration."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-wan-accelerators"
---
# Recipe Wan Accelerator Review

PREREQUISITE: Load the following utility skills first: `bakufu-wan-accelerators`

List WAN accelerators and review cache configuration.

## Relevant Commands

- `bakufu run WANAccelerators GetAllWanAccelerators --pretty`

## Instructions
- List all WAN accelerators and verify cache folder and size settings.
- Correlate WAN accelerator configuration with active backup copy jobs.
- Flag accelerators on servers with low disk space as capacity risks.
- Note: WAN accelerator management is read-only in this API version.

## Tips
- Keep WAN accelerator configuration review in quarterly infrastructure audits.
- Monitor cache utilization trends for capacity planning.
