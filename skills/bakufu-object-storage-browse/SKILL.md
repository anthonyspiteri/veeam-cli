---
name: "bakufu-object-storage-browse"
version: "1.0.0"
description: "Browse object storage regions, buckets, and folders."
metadata:
  openclaw:
    category: "helper"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-cloud-browser"
---
# Bakufu Object Storage Browse

PREREQUISITE: Load the following utility skills first: `bakufu-cloud-browser`

Browse object storage regions, buckets, and folders.

## Relevant Commands

- `bakufu call /api/v1/cloudBrowser --method POST --json @browse.json --pretty`

## Instructions
- Use browse to validate target paths before repository create/update.
- Confirm bucket and folder paths exactly match policy expectations.
- Capture discovered object hierarchy for provisioning evidence.

## Tips
- Avoid manual path assumptions in scripted onboarding.
- Use browse output to preflight automation specs.
