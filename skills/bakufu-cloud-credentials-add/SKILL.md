---
name: "bakufu-cloud-credentials-add"
version: "1.0.0"
description: "Create cloud credentials for S3-compatible storage."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-credentials"
        - "bakufu-cloud-browser"
---
# Bakufu Cloud Credentials Add

PREREQUISITE: Load the following utility skills first: `bakufu-credentials`, `bakufu-cloud-browser`

Create cloud credentials for S3-compatible storage.

## Relevant Commands

- `bakufu call /api/v1/cloudCredentials --method POST --json @creds.json --pretty`

## Instructions
- Scope credentials to required buckets and operations only.
- Test credential access with object storage browse before production use.
- Rotate credentials with change tracking and validation checks.

## Tips
- Separate read-only and management credentials where possible.
- Document ownership and rotation schedule for every secret.
