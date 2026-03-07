---
name: "bakufu-jobs"
version: "1.0.0"
description: "The Jobs section defines paths and operations for managing jobs that are coordinated by the backup server. NOTE In this version, the REST API supports the following job types&#58; `VSphereBackup` — VMware vSphere backup jobs. `vSphereReplica` — VMware vSphere replication jobs. `HyperVBackup` — Microsoft Hyper-V backup jobs. `CloudDirectorBackup` — VMware Cloud Director backup jobs. `WindowsAgentBackup` — Veeam Agent backup jobs for Microsoft Windows computers. `LinuxAgentBackup` — Veeam Agent backup jobs for Linux computers. `WindowsAgentBackupWorkstationPolicy` — Veeam Agent backup policies for Microsoft Windows computers of the workstation type. `LinuxAgentBackupWorkstationPolicy` — Veeam Agent backup policies for Linux computers of the workstation type. `WindowsAgentBackupServerPolicy` — Veeam Agent backup policies for Linux computers of the server type. `LinuxAgentBackupServerPolicy` — Veeam Agent backup policies for Linux computers of the server type. `EntraIDTenantBackup` — Microsoft Entra ID tenant backup jobs. `EntraIDAuditLogBackup` — Microsoft Entra ID audit log backup jobs. `FileBackup` — File share backup jobs. `ObjectStorageBackup` — Object storage backup jobs. `SureBackupContentScan` — SureBackup Lite jobs that perform backup verification and content scan only (full recoverability testing in virtual labs is not available). In the current version, SureBackup is supported only for backups created with Veeam Backup for Microsoft Azure, Veeam Backup for AWS, or Veeam Backup for Google Cloud. `BackupCopy` — VMware vSphere and Microsoft Hyper-V backup copy jobs. `FileBackupCopy` — Backup copy jobs for file shares. VMware vSphere jobs can process inventory objects of the following types&#58; *VirtualMachine*, *vCenterServer*, *Datacenter*, *Cluster*, *Host*, *ResourcePool*, *Folder*, *Template*, *Tag*, *Datastore* and *DatastoreCluster*. Inventory objects with multiple tags (*Multitag* type) can only be added to jobs in the Veeam Backup & Replication UI or PowerShell — the REST API only allows you to get and manage jobs that process these objects."
metadata:
  openclaw:
    category: "service"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-shared"
---
# Bakufu Jobs

PREREQUISITE: Load the following utility skills first: `bakufu-shared`

The Jobs section defines paths and operations for managing jobs that are coordinated by the backup server. NOTE In this version, the REST API supports the following job types&#58; `VSphereBackup` — VMware vSphere backup jobs. `vSphereReplica` — VMware vSphere replication jobs. `HyperVBackup` — Microsoft Hyper-V backup jobs. `CloudDirectorBackup` — VMware Cloud Director backup jobs. `WindowsAgentBackup` — Veeam Agent backup jobs for Microsoft Windows computers. `LinuxAgentBackup` — Veeam Agent backup jobs for Linux computers. `WindowsAgentBackupWorkstationPolicy` — Veeam Agent backup policies for Microsoft Windows computers of the workstation type. `LinuxAgentBackupWorkstationPolicy` — Veeam Agent backup policies for Linux computers of the workstation type. `WindowsAgentBackupServerPolicy` — Veeam Agent backup policies for Linux computers of the server type. `LinuxAgentBackupServerPolicy` — Veeam Agent backup policies for Linux computers of the server type. `EntraIDTenantBackup` — Microsoft Entra ID tenant backup jobs. `EntraIDAuditLogBackup` — Microsoft Entra ID audit log backup jobs. `FileBackup` — File share backup jobs. `ObjectStorageBackup` — Object storage backup jobs. `SureBackupContentScan` — SureBackup Lite jobs that perform backup verification and content scan only (full recoverability testing in virtual labs is not available). In the current version, SureBackup is supported only for backups created with Veeam Backup for Microsoft Azure, Veeam Backup for AWS, or Veeam Backup for Google Cloud. `BackupCopy` — VMware vSphere and Microsoft Hyper-V backup copy jobs. `FileBackupCopy` — Backup copy jobs for file shares. VMware vSphere jobs can process inventory objects of the following types&#58; *VirtualMachine*, *vCenterServer*, *Datacenter*, *Cluster*, *Host*, *ResourcePool*, *Folder*, *Template*, *Tag*, *Datastore* and *DatastoreCluster*. Inventory objects with multiple tags (*Multitag* type) can only be added to jobs in the Veeam Backup & Replication UI or PowerShell — the REST API only allows you to get and manage jobs that process these objects.

## Relevant Commands

- `bakufu services list`
- `bakufu operations --tag "Jobs"`
- `bakufu run <Tag> <OperationId> --params '{}' --pretty`
- `bakufu schema <OperationId>`

## Instructions
- Use this service skill to discover and execute operations within the same API domain.
- Start read-only (`GET`) operations first to validate scope and object identifiers.
- For write operations, run `--dry-run` when possible and capture resulting IDs.

## Tips
- Pair operation calls with `bakufu schema` to validate payloads before writes.
- Keep tag/operation mappings in runbooks for repeatable AI-agent execution.
