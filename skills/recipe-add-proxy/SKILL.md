---
name: "recipe-add-proxy"
version: "1.0.0"
description: "Add a backup proxy to the infrastructure and configure task slots."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-proxies"
        - "bakufu-managed-servers"
        - "bakufu-credentials"
---
# Recipe Add Proxy

PREREQUISITE: Load the following utility skills first: `bakufu-proxies`, `bakufu-managed-servers`, `bakufu-credentials`

Add a backup proxy to the infrastructure and configure task slots.

## Relevant Commands

- `bakufu schema CreateProxy`
- `bakufu run ManagedServers GetAllManagedServers`
- `bakufu run Proxies CreateProxy --body @proxy-spec.json`
- `bakufu run Proxies GetAllProxiesStates`

## Instructions
- Verify the managed server is added and its components are up to date before proxy creation.
- Use the schema command to discover transport mode and task-slot options.
- Set transport mode and task slots appropriate for the target workload type.
- Confirm proxy state transitions to healthy after creation.

## Tips
- Deploy proxies close to source datastores for optimal transport performance.
- Use proxy states endpoint to verify operational readiness post-deploy.
