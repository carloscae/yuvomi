#!/usr/bin/env python3
"""Minimal proof: a model served by oMLX calls Yuvomi's MCP tools. Stdlib only (runs on 3.9).

Env: YUVOMI_URL (default http://100.76.99.98:3100), YUVOMI_MCP_TOKEN,
     OMLX_URL (default http://127.0.0.1:8000), OMLX_API_KEY (optional), OMLX_MODEL.
Flow: MCP tools/list -> OpenAI-style tools -> /v1/chat/completions -> if the model
returns tool_calls, run each via MCP tools/call -> feed back -> print the final answer.
"""
import json, os, sys, urllib.request

Y = os.environ.get("YUVOMI_URL", "http://100.76.99.98:3100").rstrip("/")
O = os.environ.get("OMLX_URL", "http://127.0.0.1:8000").rstrip("/")
MODEL = os.environ.get("OMLX_MODEL", "Qwen3.8-27B-4bit")
YT = os.environ["YUVOMI_MCP_TOKEN"]
OK = os.environ.get("OMLX_API_KEY")
PROMPT = sys.argv[1] if len(sys.argv) > 1 else (
    "Use the Yuvomi tools: create a task titled 'oMLX MCP test' due 2026-10-26, "
    "then list the open tasks and tell me how many there are.")

def post(url, body, headers):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)

def mcp(method, params=None, i=[0]):
    i[0] += 1
    r = post(Y + "/mcp", {"jsonrpc": "2.0", "id": i[0], "method": method, "params": params or {}},
             {"Authorization": "Bearer " + YT, "Accept": "application/json"})
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]

mcp("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "omlx-test", "version": "0"}})
core = {"list_tasks", "create_task", "list_shopping_items", "add_shopping_item", "list_upcoming_events", "create_event"}
tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["inputSchema"]}}
         for t in mcp("tools/list")["tools"] if t["name"] in core]
oh = {"Authorization": "Bearer " + OK} if OK else {}
msgs = [{"role": "user", "content": PROMPT}]
for _ in range(6):
    r = post(O + "/v1/chat/completions", {"model": MODEL, "messages": msgs, "tools": tools, "max_tokens": 1500,
                                          "temperature": 0.2, "chat_template_kwargs": {"enable_thinking": False}}, oh)
    m = r["choices"][0]["message"]
    msgs.append({k: v for k, v in m.items() if k in ("role", "content", "tool_calls") and v is not None})
    calls = m.get("tool_calls") or []
    if not calls:
        print("FINAL:", (m.get("content") or "").strip())
        break
    for c in calls:
        fn = c["function"]
        args = json.loads(fn["arguments"] or "{}") if isinstance(fn["arguments"], str) else fn["arguments"]
        print("TOOL_CALL:", fn["name"], json.dumps(args))
        res = mcp("tools/call", {"name": fn["name"], "arguments": args})
        text = "".join(p.get("text", "") for p in res["content"])
        print("TOOL_RESULT:", text[:200].replace("\n", " "))
        msgs.append({"role": "tool", "tool_call_id": c["id"], "content": text})
