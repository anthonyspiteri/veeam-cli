---
name: "recipe-investigate-failed-job"
version: "1.0.0"
description: "Find the latest failed job session and collect logs."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-sessions"
        - "bakufu-session-logs"
        - "bakufu-session-last-failed"
---
# Recipe Investigate Failed Job

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-sessions`, `bakufu-session-logs`, `bakufu-session-last-failed`

Find the latest failed job session and collect logs.

## Relevant Commands

- `bakufu workflows investigateFailedJob --job-name "<name>"`
- `bakufu jobs list --pretty`
- `bakufu sessions show <session-id> --pretty`
- `bakufu sessions logs <session-id> --pretty`

## Instructions
- Start with the investigateFailedJob workflow to get the latest failure context.
- Pull session logs and filter to failed/warning tasks to isolate root cause.
- Correlate task-level errors with infrastructure objects (proxy, repository, host).
- Document job name, session ID, failure reason, and recommended action.

## Tips
- Check if the failure is recurring by comparing the last 3 session results.
- Attach raw session log JSON as evidence when escalating.
