# Changelog

## Unreleased — repo reorganization

Restructured the repo from a flat root layout (with several stale/duplicate files)
into the layout described in `README.md` and already assumed by the code's own
internal imports and path references.

### Moved
- `technical.py`, `sentiment.py`, `mt_bridge.py`, `registry.py`, `__init__.py` → `python/ai_trader_tools/`
- `setup.py` → `python/setup.py`
- `tool_specs.py`, `generate_manifests.py`, `openai_tools.json`, `anthropic_tools.json`,
  `mcp_tools.json` → `tools-manifest/`
- `main.py` → `rest-api/main.py`
- `server.py` → `mcp-server/server.py`
- `package.json`, `package-lock.json`, `tsconfig.json` → `node/`
- `index.ts`, `exchanges.ts`, `technical.ts`, `sentiment.ts`, `risk.ts` → `node/src/`
- `python_direct_import.py`, `openai_function_calling.py`, `node_rest_client.js` → `examples/`
- `route.ts` → `examples/nextjs-example/route.ts`

### Removed
- Root-level `exchanges.py` and `risk.py` — stale duplicates of the already-enhanced
  versions in `python/ai_trader_tools/` (connection pooling, testnet/demo support,
  input validation, richer return payloads).

### Renamed
- `download` → `.gitignore` (the file already contained `.gitignore`-style content
  under the wrong filename).
- `requirements (3).txt` → `python/requirements.txt`
- `requirements (1).txt` → `rest-api/requirements.txt`
- `requirements.txt` (root) → `mcp-server/requirements.txt`
- `Dockerfile` (root) → `mcp-server/Dockerfile`
- `Dockerfile (2)` → `rest-api/Dockerfile`

### Verified
- `python/ai_trader_tools` imports cleanly from the new layout.
- All 27 tools register correctly in `TOOL_REGISTRY`.
- Sample calls (`calc_position_size`, `calc_kelly_criterion`) run and return expected values.
- Every `.py` file passes `py_compile`.
- `tools-manifest/*.json` and `llms.txt` regenerated from `tool_specs.py` — no drift.
