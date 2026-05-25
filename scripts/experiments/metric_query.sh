#!/usr/bin/env python3
"""
POC: query local LLM with one principle at a time.

Usage: python3 metric_query.sh tests/UserManager.swift SRP
       python3 metric_query.sh tests/UserManager.swift DRY
       python3 metric_query.sh tests/UserManager.swift SRP DRY OCP
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in [ROOT/"hooks", ROOT/"mcp-server"]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hook_utils import GATEWAY
from hc_rule_loader import GatewayCommandRunner, GatewayInvoker, GatewayRuleLoader
from hc_checker import HealthPromptBuilder
from hc_llama_runner import make_llama_server_runner
from hc_config import llm_host, llm_model

if len(sys.argv) < 2:
    print(__doc__); sys.exit(1)

target = ROOT / sys.argv[1]
code   = target.read_text(encoding="utf-8")
wanted = {a.upper() for a in sys.argv[2:]}

invoker    = GatewayInvoker(GATEWAY, GatewayCommandRunner())
all_data   = GatewayRuleLoader(invoker=invoker).load_detection_rules([]) or {}
principles = [p for p in all_data.get("principles", [])
              if not wanted or p.get("name","").upper() in wanted]

if not principles:
    print("No matching principles"); sys.exit(1)

prompt = HealthPromptBuilder().build(principles, code, str(target), "")
print(f"File: {target.name}  Principles: {[p['name'] for p in principles]}  Prompt: {len(prompt)} chars\n")

result = make_llama_server_runner(host=llm_host(), model=llm_model()).run(prompt, timeout=180)
print("=" * 60)
print(result or "ERROR: no response")
