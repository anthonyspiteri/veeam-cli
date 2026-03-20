---
name: "recipe-add-repository"
version: "1.0.0"
description: "Add a new backup repository to the infrastructure."
metadata:
  openclaw:
    category: "recipe"
    requires:
      bins:
        - "bakufu"
      skills:
        - "bakufu-repositories"
        - "bakufu-managed-servers"
        - "bakufu-credentials"
---
# Recipe Add Repository

PREREQUISITE: Load the following utility skills first: `bakufu-repositories`, `bakufu-managed-servers`, `bakufu-credentials`

Add a new backup repository to the infrastructure.

## Relevant Commands

- `bakufu schema CreateRepository`
- `bakufu run ManagedServers GetAllManagedServers`
- `bakufu run Repositories CreateRepository --body @repo-spec.json`
- `bakufu run Repositories GetAllRepositories`

## Instructions
- Ensure the target managed server is added and reachable before repository creation.
- Use the schema command to validate required fields in the repository spec.
- For object storage repos, use cloud browser to preflight bucket/folder paths first.
- Run repository rescan after creation to confirm health status.

## Tips
- Set max concurrent tasks based on storage throughput capacity.
- Enable per-VM backup files for better restore granularity where supported.
