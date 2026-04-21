# Connectors

## How tool references work

This plugin is configured for the Allganize PM tool stack. The `.mcp.json` pre-configures the MCP servers listed below. On install, Claude Code will prompt you to authenticate each connector.

## Connectors for this plugin

| Category | Tool | MCP Server |
|----------|------|------------|
| Chat | Slack | slack |
| Email | Gmail | gmail |
| Project tracker | Linear | linear |

## Adding or removing connectors

Edit `.mcp.json` at the plugin root. Each entry is an HTTP MCP server:

```json
{
  "mcpServers": {
    "<name>": {
      "type": "http",
      "url": "<mcp-endpoint>"
    }
  }
}
```

After editing, run `/reload-plugins` for Claude Code to pick up the change.
