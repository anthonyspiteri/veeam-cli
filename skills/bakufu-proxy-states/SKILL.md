---
name: "bakufu-proxy-states"
version: "1.0.0"
description: "Get backup proxy states and task slot utilization."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-proxies"
---
# Bakufu Proxy States

PREREQUISITE: Load the following utility skills first: `bakufu-proxies`

Get backup proxy states and task slot utilization.

## Relevant Commands

- `bakufu run Proxies GetAllProxiesStates --pretty`
- `bakufu run Proxies GetAllProxies --pretty`

## Instructions
- Use proxy states to assess operational readiness before scheduling intensive jobs.
- Correlate proxy utilization with job throughput metrics.
- Flag proxies that are disabled or unreachable for immediate attention.

## Tips
- Include proxy health in daily infrastructure dashboards.
- Use states data to right-size task slot allocations.
