# Architecture

bakufu-cli follows the same high-level model as gws:

1. Load the Swagger spec from `/Users/anthonyspiteri/Documents/GitHub/veeam-api-agent/swagger_v1.3.json`.
2. Build a command surface from Swagger tags and operationIds.
3. Resolve parameters and path templates at runtime.
4. Execute requests via curl with OAuth tokens.
5. Emit structured JSON responses.

Key modules:

- `/Users/anthonyspiteri/Documents/GitHub/veeam-api-agent/src/bakufu_cli/swagger.py`
  - Parses tags, operations, and schemas from Swagger.
- `/Users/anthonyspiteri/Documents/GitHub/veeam-api-agent/src/bakufu_cli/token.py`
  - Obtains and caches OAuth tokens.
- `/Users/anthonyspiteri/Documents/GitHub/veeam-api-agent/src/bakufu_cli/api.py`
  - Builds and executes curl requests with pagination helpers.
- `/Users/anthonyspiteri/Documents/GitHub/veeam-api-agent/src/bakufu_cli/cli.py`
  - CLI entrypoint and dynamic command execution.

Design goals:

- Swagger-driven command surface
- Structured JSON output
- Safe dry-run mode
- Pagination support
- Skill index auto-generated from Swagger tags
