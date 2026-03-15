---
name: "bakufu-job-schedule-update"
version: "1.0.0"
description: "Update a job schedule and retention policy."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
---
# Bakufu Job Schedule Update

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`

Update a job schedule and retention policy.

## Relevant Commands

- `bakufu run Jobs GetJob --params '{"id": "<job-id>"}' --pretty`
- `bakufu run Jobs UpdateJob --params '{"id": "<job-id>"}' --json @patch.json --pretty`

## Instructions
- GET the current job configuration first; modify only schedule and retention fields.
- Preserve all non-schedule fields in the PUT payload to avoid unintended changes.
- Verify the next scheduled run time after update to confirm it took effect.

## Tips
- Keep before/after JSON diffs for change audit trails.
- Test schedule changes on a cloned job first when possible.
