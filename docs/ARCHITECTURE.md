# Architecture

bakufu-cli follows the same high-level model as the [Google Workspace CLI](https://github.com/googleworkspace/cli):

1. Load the Swagger spec from `schemas/swagger*.json` (or `BAKUFU_SWAGGER_PATH`).
2. Build a command surface from Swagger tags and operationIds.
3. Resolve parameters and path templates at runtime.
4. Execute requests via curl with OAuth tokens.
5. Emit structured output (table by default, JSON on request).

Key modules:

- `src/bakufu_cli/swagger.py`
  - Parses tags, operations, and schemas from Swagger.
- `src/bakufu_cli/token.py`
  - Obtains and caches OAuth tokens.
- `src/bakufu_cli/api.py`
  - Builds and executes curl requests with pagination helpers.
- `src/bakufu_cli/cli.py`
  - CLI entrypoint and dynamic command execution.
- `src/bakufu_cli/mcp_server.py`
  - stdio MCP server exposing service, helper, and workflow tools.
- `src/bakufu_cli/mcp_helpers.py`
  - Python-implemented helper tools with safe multi-step patterns.

Design goals:

- Swagger-driven command surface
- Structured output (table default, --json, --raw)
- Safe dry-run mode
- Pagination support
- Skill index auto-generated from Swagger tags
- MCP server mode for AI agent integration
