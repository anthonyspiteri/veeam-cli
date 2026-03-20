---
name: "recipe-add-virtualization-server"
version: "1.0.0"
description: "Add a vCenter, SCVMM, or Cloud Director server to the managed infrastructure."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-managed-servers"
        - "bakufu-inventory-browser"
        - "bakufu-managed-server-rescan"
---
# Recipe Add Virtualization Server

PREREQUISITE: Load the following utility skills first: `bakufu-managed-servers`, `bakufu-inventory-browser`, `bakufu-managed-server-rescan`

Add a vCenter, SCVMM, or Cloud Director server to the managed infrastructure.

## Relevant Commands

- `bakufu schema CreateManagedServer`
- `bakufu run ManagedServers CreateManagedServer --body @server-spec.json`
- `bakufu run ManagedServers GetManagedServer --params '{"id": "<server-id>"}'`
- `bakufu run InventoryBrowser GetVirtualInfrastructure`

## Instructions
- Use `bakufu schema CreateManagedServer` to discover required fields (hostname, credentials, type).
- Specify the server type: vCenter for vSphere, SCVMM for Hyper-V, or Cloud Director.
- Submit the server spec and capture the returned managed server ID.
- Immediately GET the server to confirm connection state and component version.
- Run inventory browse to verify that the platform hierarchy is now discoverable.
- Trigger a rescan if initial discovery returns incomplete results.
- Note: The REST API currently supports vSphere, Hyper-V, and Cloud Director. Nutanix AHV, Proxmox, and KVM are licensed platforms but managed via console/PowerShell, not the REST API.

## Tips
- Pre-validate credentials and network reachability before submitting the server spec.
- Document each platform addition with server ID, type, and credential reference.
- Schedule periodic rescans after adding new platforms to keep inventory current.
