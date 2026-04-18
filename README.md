# Trading 212 MCP Server

Python MCP server scaffold for Trading 212 read-only workflows.

## Current Status
This implementation now follows the official Trading 212 Public API v0 docs at `https://docs.trading212.com/api`.

It uses HTTP Basic authentication with `API_KEY:API_SECRET`, defaults to the paper trading base URL, and exposes only documented read-only endpoints.

## Tool Surface
- `get_account_summary`
- `list_positions`
- `list_exchanges`
- `list_instruments`
- `list_historical_orders`
- `list_dividends`
- `list_transactions`
- `list_export_reports`

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
Copy-Item .env.example .env
```

Populate `.env` using the official Trading 212 documentation, then run:

```powershell
trading212-mcp
```

## VS Code MCP Host Config
This workspace includes a VS Code MCP host config at `.vscode/mcp.json`.

It starts the server with the workspace virtual environment and loads credentials from `.env`:

```json
{
	"servers": {
		"trading212": {
			"type": "stdio",
			"command": "${workspaceFolder}/.venv/Scripts/python.exe",
			"args": ["-m", "trading212_mcp.server"],
			"envFile": "${workspaceFolder}/.env"
		}
	}
}
```

To use it in VS Code:
- Run `MCP: Open Workspace Folder MCP Configuration` to inspect the file.
- Run `MCP: List Servers` and start `trading212`.
- Approve trust when VS Code prompts for it.

## Environment Variables
See `.env.example` for the required values.

## Public Repo Notes
- Keep `.env` local and never commit Trading 212 API credentials.
- Rotate any API key immediately if you suspect it has been exposed outside your machine.
- `.vscode/mcp.json` is safe to commit because it references `${workspaceFolder}` and reads secrets from `.env`.
- This repo is designed around read-only endpoints only, which makes it safer to publish and easier to reason about.

## Notes
- This scaffold is read-only by design.
- Trading actions are intentionally excluded from v1.
- Demo base URL: `https://demo.trading212.com/api/v0`
- Live base URL: `https://live.trading212.com/api/v0`
- Historical list endpoints use cursor-based pagination with `limit` up to `50` and `nextPagePath` in the response.
