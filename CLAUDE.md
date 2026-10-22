# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An RV Park Management MCP (Model Context Protocol) server built in Python 3.12. This is a learning project exploring MCP integration with Claude, focusing on sampling, tool registration, and lifespan context management.

## Running the Project

```bash
# Start the MCP server standalone
python server.py

# Run the full client+server demo (client spawns server as subprocess)
python client.py

# Run the Claude bash tool demonstration
python bash_demo.py
```

Dependencies are managed with `uv`. To install:
```bash
uv sync
```

## Architecture

The project uses **stdio transport**: the client spawns the server as a subprocess and communicates via stdin/stdout.

**Key flow for sampling:**
1. `client.py` launches `server.py` as a subprocess
2. Client calls a tool (e.g., `summarize_guest_reviews`) via the MCP session
3. The server tool calls `ctx.session.create_message()` to make a **sampling request** — this delegates AI decision-making back to the client
4. The client's `handle_sampling` callback receives the request, asks the user for approval, then calls the Anthropic API directly
5. The response returns to the server tool, then back to the client

**Components:**
- `server.py` — MCPServer with `app_lifespan` context manager; calls `register_tools()` on startup
- `tools.py` — Three tools: `estimate_utility_costs` (external API + lifespan context), `calculate_rv_spaces` (pure math), `summarize_guest_reviews` (sampling)
- `client.py` — Async MCP client with `handle_sampling` callback implementing user-in-the-loop approval
- `bash_demo.py` — Standalone script demonstrating Claude's `bash_20250124` tool with a `MAX_API_REQUESTS` guard

## Environment Variables

Requires a `.env` file (not committed):
- `ANTHROPIC_API_KEY` — for Claude API calls in the client and bash demo
- `NEWBOOK_API_TOKEN` — for the mock external RV park API in `estimate_utility_costs`

## Key Patterns

**Lifespan context** (`server.py`): Shared state (API token) is initialized once at startup and passed to tools via `ctx.request_context.lifespan_context`.

**Sampling** (`tools.py`, `client.py`): `summarize_guest_reviews` uses `ctx.session.create_message()` rather than calling Claude directly — the server asks the client to make the AI call, keeping AI decisions under user control.

**API request limiting** (`bash_demo.py`): `MAX_API_REQUESTS` is declared as a global to cap the agentic loop.
