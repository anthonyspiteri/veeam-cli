---
name: "recipe-daily-job-health"
version: "1.0.0"
description: "Summarize success, warning, and failed jobs in the last 24 hours."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-sessions"
        - "bakufu-jobs-last-result"
---
# Recipe Daily Job Health

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-sessions`, `bakufu-jobs-last-result`

Summarize success, warning, and failed jobs in the last 24 hours.

## Relevant Commands

- `bakufu jobs list`
- `bakufu run Jobs GetAllJobsStates`
- `bakufu run Sessions GetAllSessions --params '{"limit": 100}'`

## Instructions
- List all jobs and their last result states to build the 24-hour summary.
- Categorize jobs into success, warning, and failed buckets with counts.
- Highlight any job that has not run in the expected window as potentially missed.
- Include job names and session IDs for every non-success result.

## Tips
- Run at the same time each day for comparable trend data.
- Flag jobs with warnings for 3+ consecutive days as escalation candidates.
