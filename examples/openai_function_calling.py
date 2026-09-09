"""
Example: use this toolkit's manifest with ANY standard LLM provider's function-calling /
tool-use API — this is the "normal AI provider API, not just agentic frameworks" path.
Works the same way with OpenAI, Azure OpenAI, or any OpenAI-compatible endpoint
(vLLM, Groq, Together, etc). See openai_tools.json — it's the exact `tools` array format
these APIs expect.

    pip install openai
    export OPENAI_API_KEY=...
    python3 openai_function_calling.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools-manifest"))

from openai import OpenAI
from ai_trader_tools.registry import call_tool

client = OpenAI()

with open(os.path.join(os.path.dirname(__file__), "..", "tools-manifest", "openai_tools.json")) as f:
    TOOLS = json.load(f)

messages = [{"role": "user", "content": "What's the RSI trend look like for BTC/USDT on Binance right now, 1h candles?"}]

response = client.chat.completions.create(model="gpt-4o", messages=messages, tools=TOOLS)
msg = response.choices[0].message

if msg.tool_calls:
    messages.append(msg)
    for tc in msg.tool_calls:
        args = json.loads(tc.function.arguments)
        # In this example the model will likely call get_ohlcv first, then calc_rsi in a
        # follow-up turn once it has closes — a real agent loop would keep looping until
        # there are no more tool_calls. Shown here as a single dispatch for brevity.
        result = call_tool(tc.function.name, **args)
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})

    final = client.chat.completions.create(model="gpt-4o", messages=messages, tools=TOOLS)
    print(final.choices[0].message.content)
else:
    print(msg.content)
