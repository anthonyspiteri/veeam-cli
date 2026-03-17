---
name: "recipe-add-managed-server"
version: "1.0.0"
description: "Add a vSphere, Hyper-V, Linux, or Windows server to managed infrastructure."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-managed-servers"
        - "bakufu-credentials"
        - "bakufu-connection"
---
# Recipe Add Managed Server

PREREQUISITE: Load the following utility skills first: `bakufu-managed-servers`, `bakufu-credentials`, `bakufu-connection`

Add a vSphere, Hyper-V, Linux, or Windows server to managed infrastructure.

## Relevant Commands

- `bakufu schema CreateManagedServer`
- `bakufu run Connection GetConnectionCertificate --params '{"host": "<server>"}' --pretty`
- `bakufu run ManagedServers CreateManagedServer --json @server-spec.json --pretty`
- `bakufu run ManagedServers GetAllManagedServers --pretty`

## Instructions
- Retrieve the TLS certificate or SSH fingerprint first and include it in the spec for trust.
- Resolve or create credentials before referencing them in the server spec.
- Verify the server type matches the actual platform (vSphere, HyperV, Linux, Windows).
- Run rescan after adding to confirm component deployment completed.

## Tips
- Use dedicated credentials for hardened Linux repositories.
- Document server additions with their credential IDs for rotation tracking.
