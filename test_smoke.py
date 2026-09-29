# -*- coding: utf-8 -*-
"""晋迹 · 冒烟自测（不依赖网络与 API Key，走 MOCK 模式）"""
import os
os.environ["MOCK_LLM"] = "1"

import kb
import agent
import config

print("知识库：", len(kb.ATTRACTIONS), "处古建 /", len(kb.ROUTES), "条路线")
print("MOCK 模式：", config.MOCK)

for q in ["黑神话悟空在山西的取景地有哪些", "应县木塔", "晋北古建", "唐代木构", "晋商大院"]:
    hits = [a["name"] for a in kb.retrieve(q)]
    print(f"检索[{q}] -> {hits}")

for q in ["讲解应县木塔为什么千年不倒", "帮我规划晋北 2 日古建游"]:
    reply, steps = agent.run_agent(q, [])
    print(f"\n提问：{q}")
    for s in steps:
        print("  工具调用：", s["name"], s["args"])
        print("  结果摘要：", str(s["result"])[:100])
    print("  回答：", reply[:80])

print("\nSMOKE_OK")
