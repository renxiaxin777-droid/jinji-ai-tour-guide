# -*- coding: utf-8 -*-
"""证据采集用开发页：普通大模型「直答」（无知识库、无工具）—— 与晋迹形成对照实验。

用途：为设计文档/视频提供「套壳聊天 vs 工具调用智能体」的真实对比截图。
不属于作品功能，仅作对比材料。运行：streamlit run tools/plain_llm_demo.py --server.port 8527
"""
import json
import os
import sys
import urllib.request

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

st.set_page_config(page_title="对照实验 · 普通大模型直答", page_icon="🤖", layout="wide")
st.markdown("<h3>🤖 对照实验 · 普通大模型直答（无知识库、无工具）</h3>",
            unsafe_allow_html=True)
st.caption("输入同一个问题，观察模型在没有任何资料约束下的直接回答。")

if "h" not in st.session_state:
    st.session_state.h = []

q = st.chat_input("向普通大模型提问…")
if q:
    msgs = ([{"role": "system", "content": "你是一名普通的中文AI助手，直接回答用户问题。"}]
            + st.session_state.h
            + [{"role": "user", "content": q}])
    body = {"model": config.MODEL, "messages": msgs,
            "temperature": config.TEMPERATURE, "stream": False}
    req = urllib.request.Request(
        config.API_BASE + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + config.API_KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())["choices"][0]["message"]["content"]
    st.session_state.h += [{"role": "user", "content": q},
                           {"role": "assistant", "content": out}]
    st.rerun()

for m in st.session_state.h:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
