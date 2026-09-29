"""晋迹 · 现代版界面 Demo（shadcn-ui 组件 + 重设计规范）

与 app.py 的差异（对照 experiment）：
  · 排版：衬线标题（古建气质）+ 无衬线正文，字重分层（500/600/700）
  · 配色：单一强调色 朱红 #A03A2C，暖灰中性色，浅渐变 + 单光晕 + 单细环
  · 组件：shadcn-ui 的 metric_card / badge / card / collapsible 替代原生裸组件
  · 文案：去掉感叹号与营销词，指标用真实数据
功能逻辑与 app.py 完全一致（复用 agent / kb / config）。
"""
import hashlib
import json
import os
import tempfile

import streamlit as st
import streamlit_shadcn_ui as ui

import agent
import config
import kb

st.set_page_config(page_title="晋迹 · 山西古建智能导览体", page_icon="🏯", layout="wide")

# ---------------- 设计系统（重设计规范落地） ----------------
st.markdown("""
<style>
:root{
  --ink:#2B2622; --ink-soft:#6B6157; --ink-faint:#9A8F82;
  --accent:#A03A2C; --accent-soft:rgba(160,58,44,.10);
  --paper:#FDFBF6; --paper-2:#F7F1E6; --line:#E8DCC8;
  --serif:"Noto Serif SC","Source Han Serif SC","Songti SC",SimSun,Georgia,serif;
  --sans:"PingFang SC","HarmonyOS Sans SC","Microsoft YaHei",-apple-system,system-ui,sans-serif;
}
/* 背景：浅渐变 + 单光晕（不做 45° 均匀渐变） */
.stApp{
  background:
    radial-gradient(880px 460px at 88% -12%, var(--accent-soft), transparent 62%),
    linear-gradient(178deg, var(--paper) 0%, var(--paper-2) 100%);
  font-family: var(--sans); color: var(--ink);
}
.block-container{padding-top:2.6rem; max-width:1080px}

/* 装饰细环：单只，右上方，不与内容打架 */
.stApp::before{
  content:""; position:fixed; top:64px; right:-90px; width:280px; height:280px;
  border:1px solid rgba(160,58,44,.16); border-radius:50%; pointer-events:none;
}

h1,h2,h3{font-family:var(--serif); color:var(--ink); font-weight:600; letter-spacing:-.01em}
.hero-title{font-family:var(--serif); font-size:3.05rem; font-weight:700; line-height:1.04;
  letter-spacing:-.02em; margin:0 0 .35rem 0; color:var(--ink)}
.hero-title .accent{color:var(--accent)}
.hero-sub{font-size:1.02rem; line-height:1.7; color:var(--ink-soft); max-width:64ch; margin:0}
.hero-rule{height:1px; background:linear-gradient(90deg,var(--line),transparent); margin:1.4rem 0 1.6rem 0}

/* 聊天：卡片化但保留浮起层次，圆角不一刀切 */
[data-testid="stChatMessage"]{
  background:#FFFDF9; border:1px solid var(--line); border-radius:16px 16px 16px 6px;
  padding:.35rem .2rem; box-shadow:0 1px 2px rgba(80,60,40,.04);
}
[data-testid="stChatMessage"] p{line-height:1.75}
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#F7F1E6,#F3EADB);
  border-right:1px solid var(--line);
}
[data-testid="stSidebar"] .stButton>button{
  width:100%; text-align:left; background:#FFFDF9; border:1px solid var(--line);
  color:var(--ink); border-radius:12px; padding:.55rem .8rem; font-size:.9rem;
  transition:transform .18s ease, border-color .18s ease, background .18s ease;
}
[data-testid="stSidebar"] .stButton>button:hover{
  border-color:var(--accent); background:#fff; transform:translateY(-1px);
}
[data-testid="stSidebar"] .stButton>button:active{transform:translateY(0) scale(.99)}
.stButton>button{border-radius:10px; transition:all .18s ease}
.stButton>button:hover{border-color:var(--accent); color:var(--accent)}
/* 标签/小字统一 tracking，小字加宽字距 */
.tag{display:inline-block; font-size:.72rem; letter-spacing:.08em; text-transform:uppercase;
  color:var(--ink-faint); border:1px solid var(--line); border-radius:999px; padding:.2rem .6rem}
.wf-step{border-left:2px solid var(--accent-soft); padding:.1rem 0 .1rem .8rem; margin:.45rem 0}
.wf-step b{font-weight:600}
.wf-step code{background:#F4EBDD; border:none; color:#7A3226; font-size:.8rem}
.wf-step .res{display:block; color:var(--ink-faint); font-size:.78rem; margin-top:.15rem;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.foot{color:var(--ink-faint); font-size:.78rem; letter-spacing:.02em}
</style>
""", unsafe_allow_html=True)

# ---------------- 主区：Hero ----------------
st.markdown(
    '<div class="tag">华北五省大学生计算机应用大赛 · 大模型与智能体应用赛道</div>'
    '<p style="height:.5rem;margin:0"></p>'
    '<h1 class="hero-title">晋迹<span class="accent">.</span></h1>'
    '<p class="hero-sub">山西古建智能导览体 —— 会查资料、会排行程、会讲古建故事。'
    '回答之前先检索知识库，让每一句讲解都有出处。</p>'
    '<div class="hero-rule"></div>',
    unsafe_allow_html=True,
)

# ---------------- 指标卡（真实数据） ----------------
c1, c2, c3, c4 = st.columns(4, gap="small")
with c1:
    ui.metric_card("古建条目", f"{len(kb.ATTRACTIONS)}", description="收录于本地知识库", key="m1")
with c2:
    ui.metric_card("精选路线", f"{len(kb.ROUTES)}", description="晋北 · 晋中 · 黑神话巡礼", key="m2")
with c3:
    ui.metric_card("可调用工具", "3", description="检索 · 详情 · 行程规划", key="m3")
with c4:
    ui.metric_card("模型", "DeepSeek", description=f"{config.MODEL} · 国产大模型", key="m4")

st.markdown('<p style="height:.9rem;margin:0"></p>', unsafe_allow_html=True)

# ---------------- 侧栏：控制台 ----------------
st.sidebar.markdown(
    '<h3 style="font-family:var(--serif);margin:.2rem 0 .1rem 0">导览控制台</h3>'
    '<p class="foot" style="margin:0 0 .9rem 0">快捷提问 · 一键体验三条主线</p>',
    unsafe_allow_html=True,
)
if config.MOCK:
    st.sidebar.info("离线演示模式：未配置 API Key，仍可完整走通智能体流程")
else:
    st.sidebar.success(f"DeepSeek 已连接 · {config.MODEL}")

st.sidebar.markdown('<p class="foot" style="margin:1rem 0 .3rem 0">快捷提问</p>', unsafe_allow_html=True)
for q in ["帮我规划晋北 2 日古建游", "讲解应县木塔为什么千年不倒", "黑神话悟空在山西的取景地有哪些"]:
    if st.sidebar.button(q, key=f"q_{q}"):
        st.session_state["pending"] = q
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p class="foot">工具链路：提问 → 大模型判断 → 调用知识库工具 → 组织讲解 → 语音播报</p>',
    unsafe_allow_html=True,
)

# ---------------- 会话状态 ----------------
if "history" not in st.session_state:
    st.session_state["history"] = []
history = st.session_state["history"]


# 演示预置：访问 ?demo=1 直接进入"已有对话"状态（截图/彩排用，不改默认行为）
if st.query_params.get("demo") == "1" and not history:
    _q = "帮我规划晋北 2 日古建游"
    try:
        _reply, _steps = agent.run_agent(_q, [])
    except Exception as _e:  # noqa: BLE001
        _reply, _steps = f"出错了：{_e}", []
    history.append({"role": "user", "content": _q})
    history.append({"role": "assistant", "content": _reply, "steps": _steps})


def tts_file(text):
    key = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    path = os.path.join(tempfile.gettempdir(), f"jinji_tts_{key}.mp3")
    if not os.path.exists(path):
        import asyncio
        import edge_tts
        asyncio.run(edge_tts.Communicate(text[:500], "zh-CN-YunxiNeural").save(path))
    return path


def render_steps(steps, key):
    """智能体工作流：用左侧细线 + 等宽参数，视觉上像一条执行链"""
    with st.expander(f"智能体工作流 · {len(steps)} 次工具调用", expanded=False):
        for i, s in enumerate(steps):
            st.markdown(
                f'<div class="wf-step"><b>{s["name"]}</b> '
                f'<code>{json.dumps(s["args"], ensure_ascii=False)}</code>'
                f'<span class="res">{str(s["result"])[:180]}</span></div>',
                unsafe_allow_html=True,
            )


# ---------------- 历史消息 ----------------
if not history:
    st.markdown(
        '<p class="foot" style="margin-top:.4rem">还没有对话 —— 从左侧选一条快捷提问，或直接在下方输入。</p>',
        unsafe_allow_html=True,
    )

for i, h in enumerate(history):
    with st.chat_message(h["role"], avatar="🧭" if h["role"] == "assistant" else "🧳"):
        if h["role"] == "assistant" and h.get("steps"):
            render_steps(h["steps"], f"h{i}")
        st.markdown(h["content"])
        if h["role"] == "assistant" and len(h["content"]) > 10:
            if st.button("语音讲解", key=f"tts_{i}"):
                with st.spinner("合成语音中…"):
                    try:
                        st.audio(tts_file(h["content"]), format="audio/mp3")
                    except Exception as e:  # noqa: BLE001
                        st.warning(f"语音合成失败：{e}")

# ---------------- 输入 ----------------
inp = st.chat_input("问问晋迹：景点讲解 / 行程规划 / 拍照机位…")
pending = st.session_state.pop("pending", None)
if inp or pending:
    text = inp or pending
    history.append({"role": "user", "content": text})
    with st.chat_message("user", avatar="🧳"):
        st.markdown(text)
    with st.chat_message("assistant", avatar="🧭"):
        with st.spinner("晋迹正在查阅资料、调用工具…"):
            try:
                reply, steps = agent.run_agent(
                    text,
                    [{"role": h["role"], "content": h["content"]} for h in history[:-1]],
                )
            except Exception as e:  # noqa: BLE001
                reply, steps = f"出错了：{e}", []
        if steps:
            render_steps(steps, "live")
        st.markdown(reply)
    history.append({"role": "assistant", "content": reply, "steps": steps})
    st.rerun()
