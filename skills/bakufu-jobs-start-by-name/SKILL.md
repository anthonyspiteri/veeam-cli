---
name: "bakufu-jobs-start-by-name"
version: "1.0.0"
description: "Start a job by name and return session details."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-sessions"
---
# Bakufu Jobs Start By Name

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-sessions`

Start a job by name and return session details.

## Relevant Commands

- `bakufu jobs list`
- `bakufu workflows investigateFailedJob --job-name "<name>"`

## Instructions
- Resolve the exact job name before start to avoid launching the wrong workload.
- Capture returned session identifiers for follow-up checks.
- Immediately verify resulting session state and logs if state is non-success.

## Tips
- Use account override for multi-tenant environments.
- Prefer name-based start in operator runbooks where IDs are unstable.
