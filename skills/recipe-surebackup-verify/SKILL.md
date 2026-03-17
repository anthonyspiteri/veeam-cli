---
name: "recipe-surebackup-verify"
version: "1.0.0"
description: "Run SureBackup verification scan on backups and track completion."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-jobs"
        - "bakufu-sessions"
        - "bakufu-session-follow"
---
# Recipe Surebackup Verify

PREREQUISITE: Load the following utility skills first: `bakufu-jobs`, `bakufu-sessions`, `bakufu-session-follow`

Run SureBackup verification scan on backups and track completion.

## Relevant Commands

- `bakufu jobs list --pretty`
- `bakufu run Jobs StartJob --params '{"id": "<surebackup-job-id>"}' --pretty`
- `bakufu sessions show <session-id> --pretty`
- `bakufu sessions logs <session-id> --pretty`

## Instructions
- Identify existing SureBackupContentScan jobs or create one for the target backups.
- Start the SureBackup job and capture the returned session ID.
- Follow the session to terminal state and capture verification results.
- Correlate verification failures with specific backup objects and restore points.
- Note: SureBackup is currently supported for Azure, AWS, and GCP cloud backups only.

## Tips
- Schedule SureBackup jobs after primary backup windows complete.
- Track verification pass rates over time as a recoverability confidence metric.
- Retain SureBackup session logs as recovery readiness evidence.
