---
name: "bakufu-job-create"
version: "1.0.0"
description: "Create a new backup job from a JSON spec."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-repositories"
        - "bakufu-inventory-browser"
---
# Bakufu Job Create

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-repositories`, `bakufu-inventory-browser`

Create a new backup job from a JSON spec.

## Relevant Commands

- `bakufu run Jobs CreateJob --json @job-spec.json --pretty`
- `bakufu schema CreateJob`

## Instructions
- Validate the job spec against the schema before submission.
- Ensure referenced repository, credentials, and inventory objects exist.
- Capture the returned job ID for downstream verification.

## Tips
- Store job specs as versioned files for repeatable deployment.
- Use schema command to discover required and optional fields.
