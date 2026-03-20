---
name: "recipe-clone-job"
version: "1.0.0"
description: "Clone an existing backup job for testing or migration."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-job-by-name"
---
# Recipe Clone Job

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-job-by-name`

Clone an existing backup job for testing or migration.

## Relevant Commands

- `bakufu jobs list`
- `bakufu run Jobs CloneJob --params '{"id": "<job-id>"}'`
- `bakufu run Jobs GetJob --params '{"id": "<cloned-job-id>"}'`

## Instructions
- Resolve the source job by name or ID before cloning.
- Capture the returned cloned job ID and verify its full configuration.
- Disable the cloned job schedule immediately if this is for testing only.
- Rename or annotate the clone to distinguish it from the original.

## Tips
- Use clone to safely test schedule, retention, or target changes before modifying production.
- Delete test clones promptly to avoid accidental production runs.
