---
name: "recipe-create-backup-job"
version: "1.0.0"
description: "Create a new backup job with VMs, repository, and schedule."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-repositories"
        - "bakufu-inventory-browser"
---
# Recipe Create Backup Job

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-repositories`, `bakufu-inventory-browser`

Create a new backup job with VMs, repository, and schedule.

## Relevant Commands

- `bakufu schema CreateJob`
- `bakufu run InventoryBrowser GetVirtualInfrastructure`
- `bakufu run Repositories GetAllRepositories`
- `bakufu run Jobs CreateJob --body @job-spec.json`
- `bakufu run Jobs GetJob --params '{"id": "<job-id>"}'`

## Instructions
- Use `bakufu schema CreateJob` to discover required and optional fields before building the spec.
- Browse inventory to resolve VM, container, or tag object IDs for the job source.
- Validate that the target repository exists and has sufficient capacity.
- Submit the job spec and capture the returned job ID.
- Immediately GET the created job to confirm all settings were applied correctly.

## Tips
- Store job specs as versioned JSON files for repeatable deployment.
- Test with a single VM before scaling to full workload sets.
- Verify guest processing credentials if application-aware processing is enabled.
