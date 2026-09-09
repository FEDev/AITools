"""
Run this after editing tool_specs.py:

    python3 generate_manifests.py

Regenerates:
    openai_tools.json
    anthropic_tools.json
    mcp_tools.json
    ../llms.txt
"""
import json
import os
from tool_specs import TOOLS, SUPPORTED_EXCHANGES

HERE = os.path.dirname(os.path.abspath(__file__))


def build_openai():
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in TOOLS
    ]


def build_anthropic():
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in TOOLS
    ]


def build_mcp():
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "inputSchema": t["parameters"],
        }
        for t in TOOLS
    ]


def build_llms_txt():
    lines = [
        "# AI Trader Tools — llms.txt",
        "",
        "Open-source, MIT-licensed toolkit of callable functions for building AI/LLM-driven trading",
        "agents. Feed this whole file (or tools-manifest/openai_tools.json /",
        "tools-manifest/anthropic_tools.json) to any LLM that supports function/tool calling and it",
        "will know every tool available, its parameters, and what it returns.",
        "",
        "Three ways to consume this toolkit:",
        "  1. Direct import  — python/ai_trader_tools (pip) or node/ (npm), no server needed.",
        "  2. REST API       — rest-api/main.py (FastAPI). POST /tools/{tool_name} with a JSON body.",
        "                       Works from Next.js, any Node app, curl, or any HTTP-capable AI agent.",
        "  3. MCP server      — mcp-server/server.py. stdio or HTTP/SSE transport for MCP-aware agents",
        "                       (Claude Desktop, Claude Code, etc).",
        "",
        f"Supported crypto exchanges (via ccxt, unified API): {', '.join(SUPPORTED_EXCHANGES)}.",
        "Plus an MT5 bridge for forex / XAUUSD / indices (requires a running MetaTrader 5 terminal).",
        "",
        "This is general-purpose open-source infrastructure, not financial advice, and ships with no",
        "API keys or credentials. Anyone may use, fork, or modify it (MIT license).",
        "",
        "## Tool catalog",
        "",
    ]
    by_cat = {}
    for t in TOOLS:
        by_cat.setdefault(t["category"], []).append(t)
    for cat, tools in by_cat.items():
        lines.append(f"### {cat}")
        lines.append("")
        for t in tools:
            req = t["parameters"].get("required", [])
            props = t["parameters"].get("properties", {})
            param_str = ", ".join(
                f"{p}{'*' if p in req else ''}" for p in props
            ) or "(none)"
            lines.append(f"- **{t['name']}** — {t['description']}")
            lines.append(f"  - params: {param_str}  (`*` = required)")
            lines.append(f"  - implementation: `{t['implementation']}`")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    with open(os.path.join(HERE, "openai_tools.json"), "w") as f:
        json.dump(build_openai(), f, indent=2)
    with open(os.path.join(HERE, "anthropic_tools.json"), "w") as f:
        json.dump(build_anthropic(), f, indent=2)
    with open(os.path.join(HERE, "mcp_tools.json"), "w") as f:
        json.dump(build_mcp(), f, indent=2)
    with open(os.path.join(HERE, "..", "llms.txt"), "w") as f:
        f.write(build_llms_txt())
    print(f"Generated manifests for {len(TOOLS)} tools.")
