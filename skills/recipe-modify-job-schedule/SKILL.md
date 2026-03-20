---
name: "recipe-modify-job-schedule"
version: "1.0.0"
description: "Update an existing job schedule and retention settings."
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
# Recipe Modify Job Schedule

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-job-by-name`

Update an existing job schedule and retention settings.

## Relevant Commands

- `bakufu jobs list`
- `bakufu run Jobs GetJob --params '{"id": "<job-id>"}'`
- `bakufu run Jobs UpdateJob --params '{"id": "<job-id>"}' --body @schedule-patch.json`

## Instructions
- Resolve the job by name or ID first, then GET its current full configuration.
- Modify only the schedule and retention fields; preserve all other job settings in the PUT payload.
- Validate the updated schedule does not conflict with other jobs in the same backup window.
- Capture before and after JSON snapshots for change audit trails.
- Verify the next scheduled run time after update to confirm it took effect.

## Tips
- Use job clone as a safer alternative to test schedule changes on a copy first.
- Keep before/after JSON diffs in change management records.
