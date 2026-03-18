---
name: "recipe-platform-inventory-browse"
version: "1.0.0"
description: "Browse virtualization infrastructure hierarchy (vSphere, Hyper-V, Cloud Director) and list managed objects."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-inventory-browser"
        - "bakufu-managed-servers"
---
# Recipe Platform Inventory Browse

PREREQUISITE: Load the following utility skills first: `bakufu-inventory-browser`, `bakufu-managed-servers`

Browse virtualization infrastructure hierarchy (vSphere, Hyper-V, Cloud Director) and list managed objects.

## Relevant Commands

- `bakufu run InventoryBrowser GetVirtualInfrastructure --pretty`
- `bakufu run InventoryBrowser GetVmwareHosts --params '{"hostId": "<host-id>"}' --pretty`
- `bakufu run ManagedServers GetAllManagedServers --pretty`

## Instructions
- List all virtualization servers to identify vSphere, Hyper-V, and Cloud Director platforms.
- Drill into each platform to enumerate datacenters, clusters, hosts, and VMs.
- Cross-reference inventory objects with managed server entries to verify connectivity.
- Use inventory browsing to validate VM object IDs before assigning them to backup jobs.
- Note: Inventory browsing covers vSphere, Hyper-V, and Cloud Director. Nutanix AHV, Proxmox, and KVM workloads appear in license data but are not browsable via the REST API.

## Tips
- Run inventory browsing after adding or rescanning virtualization servers to confirm discovery.
- Use inventory hierarchy to plan scope for new backup jobs by cluster or resource pool.
- Compare inventory object counts across runs to detect VM sprawl or decommissions.
