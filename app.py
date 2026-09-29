"""晋迹 · 山西古建智能导览体 —— Streamlit 前端"""
import base64
import hashlib
import json
import os
import tempfile

import streamlit as st

import agent
import config
import kb

st.set_page_config(page_title="晋迹·AI古建导览", page_icon="🏯", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.loli.net/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
  font-family: 'Noto Serif SC', 'Songti SC', 'SimSun', '宋体', serif;
}
.stApp { background: #F5EFE6; }
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(120% 90% at 85% -8%, rgba(196,163,90,0.10), transparent 55%),
    radial-gradient(90% 70% at 5% 108%, rgba(42,75,92,0.06), transparent 55%),
    #F5EFE6;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: #FBF7EE;
  border-right: 1px solid rgba(196,163,90,0.35);
}
.block-container { padding-top: 2.2rem; max-width: 1050px; }

h1, h2, h3 {
  color: #5C3A21;
  font-family: 'Ma Shan Zheng', 'KaiTi', 'STKaiti', '楷体', serif;
  font-weight: 400;
}
h1 { letter-spacing: 0.06em; }

[data-testid="stChatMessage"] {
  background: rgba(255,255,255,0.82);
  border: 1px solid rgba(196,163,90,0.35);
  border-radius: 14px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: #5C3A21;
  color: #FBF7EE;
  border-color: #5C3A21;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) li {
  color: #FBF7EE !important;
}

.stButton > button, .stDownloadButton > button {
  background: #C4A35A;
  color: #4A2E17;          /* 深棕字：与金底对比度 5.2:1，达 WCAG AA（原白字仅 2.4:1） */
  border: none;
  border-radius: 999px;
}
.stButton > button:hover { background: #b28f43; }

/* 侧边栏状态条：与宣纸/檀木/古铜金同色系，替代 Streamlit 默认绿框 */
.stat-bar { border-radius: 10px; padding: 9px 12px; font-size: 13px; letter-spacing: .02em; }
.stat-bar.ok { background: rgba(196,163,90,.16); border: 1px solid rgba(196,163,90,.45); color: #5C3A21; }
.stat-bar.warn { background: rgba(42,75,92,.10); border: 1px solid rgba(42,75,92,.28); color: #2A4B5C; }
.stat-bar .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%;
  background: #7C9A54; margin-right: 7px; vertical-align: 1px; }

/* 输入框占位符加深（默认灰度过低，演示与截图时几乎看不见） */
[data-testid="stChatInput"] textarea::placeholder { color: #94826a !important; opacity: 1 !important; }

/* 空状态引导卡：首屏无对话时展示「三条主线」 */
.guide-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 12px 0 8px; }
.guide-card { background: rgba(255,255,255,.60); border: 1px solid rgba(196,163,90,.42);
  border-radius: 12px; padding: 16px 18px 12px; }
.guide-card .t { font-family: 'Ma Shan Zheng', KaiTi, serif; color: #5C3A21; font-size: 20px; letter-spacing: .04em; }
.guide-card .d { color: #7a6a55; font-size: 13px; line-height: 1.75; margin-top: 6px; min-height: 46px; }
[data-testid="stSidebar"] .stButton > button {
  background: rgba(196,163,90,0.14);
  color: #5C3A21;
  border: 1px solid rgba(196,163,90,0.4);
}
[data-testid="stSidebar"] .stButton > button:hover { background: rgba(196,163,90,0.26); }

[data-testid="stExpander"] {
  border: 1px solid rgba(196,163,90,0.3);
  border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- 落地页（首页） ----------------
if not st.session_state.get("started", False):
    _hero_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "assets", "hero-roof.jpg")
    _b64 = ""
    if os.path.exists(_hero_path):
        with open(_hero_path, "rb") as _f:
            _b64 = base64.b64encode(_f.read()).decode()
    _bg = f"url(data:image/jpeg;base64,{_b64})" if _b64 else "linear-gradient(160deg,#1F3A40,#2C4A4F)"
    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ display: none; }}
    [data-testid="stAppViewContainer"] {{ background: {_bg} center / cover no-repeat, #2C4A4F; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 2rem; }}
    .stButton {{ margin-top: 14px !important; }}
    .stButton > button {{
      font-size: 21px !important; padding: 15px 46px !important;
      border-radius: 8px !important; letter-spacing: 0.18em !important;
      font-family: 'Ma Shan Zheng', KaiTi, serif !important;
      background: #C4A35A !important; color: #4A2E17 !important;
      border: 1px solid #B8860B !important;
    }}
    .stButton > button:hover {{ background: #b28f43 !important; }}
    </style>
    <div style="padding-top:7vh">
      <div style="background:rgba(241,232,214,0.80);backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px);padding:40px 46px 34px;border-radius:8px;max-width:460px;box-shadow:0 10px 34px rgba(0,0,0,0.28)">
        <div style="font-family:'Ma Shan Zheng',KaiTi,serif;color:#C89B3C;font-size:76px;line-height:1;text-shadow:1px 2px 3px rgba(0,0,0,0.2)">晋迹</div>
        <div style="color:#8a6a2a;letter-spacing:0.32em;margin-top:12px;font-size:15px">山西古建 · 智能导览</div>
        <p style="color:#5a4a20;line-height:1.8;margin-top:20px;font-size:15px">会查资料、会排行程、会讲古建故事。收录 <b>35 处</b>重点古建与 <b>5 条</b>精选路线。</p>
      </div>
      <div style="display:inline-block;background:rgba(241,232,214,0.78);color:#5a4a20;font-size:12px;margin-top:18px;letter-spacing:0.05em;padding:7px 16px;border-radius:6px">华北五省大学生计算机应用大赛 · 大模型与智能体应用赛道</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("开始山西之旅", type="primary"):
        st.session_state["started"] = True
        st.rerun()
    st.stop()

st.markdown(
    "<h1>晋迹 · 山西古建智能导览体</h1>"
    "<p style='color:#7a6a55;font-size:1rem'>会查资料、会排行程、会讲古建故事的大模型导览智能体。"
    "带你读懂三晋大地上的千年营造。</p>",
    unsafe_allow_html=True,
)

# ---------------- 侧边栏 ----------------
st.sidebar.title("🧭 导览控制台")
if config.MOCK:
    st.sidebar.markdown(
        '<div class="stat-bar warn">离线演示模式 · 未配置 API Key，仍可走完整智能体流程</div>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        f'<div class="stat-bar ok"><span class="dot"></span>DeepSeek 已连接 · {config.MODEL}</div>',
        unsafe_allow_html=True,
    )
st.sidebar.caption(
    f"本地知识库收录 {len(kb.ATTRACTIONS)} 处山西古建 · {len(kb.ROUTES)} 条精选路线\n\n"
    "「晋迹」是一个工具调用型智能体：回答前先检索知识库、规划前先调路线工具，"
    "保证讲解有据可依。"
)
_level_label = st.sidebar.radio("🎓 导览模式", ["小白导览", "进阶讲解", "硬核断代", "🧭 行程规划师"], index=0)
LEVEL_KEYS = {"小白导览": "basic", "进阶讲解": "pro", "硬核断代": "hardcore", "🧭 行程规划师": "planner"}
level = LEVEL_KEYS[_level_label]
if level == "hardcore":
    st.sidebar.caption("硬核模式：含建筑形制术语 + 断代依据 + 学界争议")
if level == "planner":
    st.sidebar.caption("行程规划师：逐构件读古建 + 精确时间轴 + 门票食宿实操")
st.sidebar.markdown("**✨ 快捷提问**")
for q in ["帮我规划晋北 2 日古建游", "帮我排一条木构断代演变之旅", "讲解应县木塔为什么千年不倒", "黑神话悟空在山西的取景地有哪些"]:
    if st.sidebar.button(q, use_container_width=True):
        st.session_state["pending"] = q
        st.rerun()

with st.sidebar.expander("📚 数据来源与 AI 声明"):
    st.caption(
        "知识库内容整理自全国重点文物保护单位名录等公开资料，经人工校对。\n\n"
        "本作品按大赛要求声明：开发过程使用 DeepSeek 大模型辅助编程与文案生成；"
        "作品创意、功能设计、知识库与检索策略、测试验收为团队原创设计。"
    )
_up = st.sidebar.file_uploader("📷 拍照识古建（实验功能）", type=["jpg", "jpeg", "png", "webp"])
if _up is not None:
    if st.sidebar.button("🔍 识别这张照片", use_container_width=True):
        st.session_state["photo"] = _up.getvalue()
        st.session_state["photo_mime"] = _up.type
        st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("华北五省大学生计算机应用大赛 · 大模型与智能体应用赛道")

# ---------------- 历史消息渲染 ----------------
if "history" not in st.session_state:
    st.session_state["history"] = []
history = st.session_state["history"]


TTS_VOICE = "zh-CN-XiaoxiaoNeural"  # edge-tts 女声·晓晓（首选，音质佳）


def _strip_md(text):
    """朗读前剥离 Markdown 符号（纯文本进纯文本出，幂等，不依赖网络）"""
    import re
    t = text
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", t)          # 图片 ![alt](url)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)          # 链接 [文字](url)
    t = re.sub(r"`([^`]*)`", r"\1", t)                       # 行内代码 `x`
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)                 # 粗体 **x**
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", t)        # 斜体 *x*
    t = re.sub(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$", "", t, flags=re.M)  # 表头分隔线
    t = t.replace("|", "，")                                  # 表格竖线 → 停顿
    t = re.sub(r"^\s*#{1,6}\s*", "", t, flags=re.M)          # 标题 # ## ...
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)           # 无序列表 - / * / +
    t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.M)           # 有序列表 1. 2.
    t = re.sub(r"^\s*>\s?", "", t, flags=re.M)               # 引用 >
    t = re.sub(r"^\s*(-{3,}|_{3,}|\*{3,})\s*$", "", t, flags=re.M)  # 分隔线
    t = re.sub(r"<[^>]+>", "", t)                            # HTML 标签
    t = re.sub(r"\n{3,}", "\n\n", t)                         # 压缩空行
    return t.strip()


def _local_tts(text):
    """本地离线语音（Windows SAPI 女声 Huihui），零网络兜底"""
    import pyttsx3
    engine = pyttsx3.init()
    for v in engine.getProperty("voices"):
        if "Chinese" in v.name or "ZH-CN" in v.id.upper():
            engine.setProperty("voice", v.id)
            break
    engine.setProperty("rate", 170)
    key = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
    path = os.path.join(tempfile.gettempdir(), f"jinji_tts_local_{key}.wav")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        engine.save_to_file(text[:500], path)
        engine.runAndWait()
    return path


def tts_file(text):
    """合成语音：优先 edge-tts 女声（mp3），网络失败自动退本地 SAPI 女声（wav）。
    返回 (路径, mime)。缓存按文件大小校验，规避断流遗留的 0 字节文件。"""
    text = _strip_md(text)  # 朗读前剥离 Markdown 符号（# ** - ` | > 等）
    import asyncio
    import time

    import edge_tts
    key = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    path = os.path.join(tempfile.gettempdir(), f"jinji_tts_{key}.mp3")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        last = None
        for attempt in range(3):
            try:
                asyncio.run(edge_tts.Communicate(text[:500], TTS_VOICE).save(path))
                if os.path.getsize(path) > 0:
                    return path, "audio/mp3"
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(1 + attempt)
        if os.path.exists(path) and os.path.getsize(path) == 0:
            os.remove(path)  # 清掉断流遗留的 0 字节文件
        try:  # 兜底：本地离线女声，保证决赛现场零网络也能播
            return _local_tts(text), "audio/wav"
        except Exception:  # noqa: BLE001
            raise last
    return path, "audio/mp3"


# ---------------- 空状态引导（首屏无对话时展示三条主线 + 可点示例） ----------------
if not history:
    _GUIDES = [
        ("会查资料", "先检索知识库、再基于资料作答，不编造年代数据。",
         "黑神话悟空在山西的取景地有哪些"),
        ("会排行程", "按天数、城市与兴趣编排路线，覆盖晋北到晋南。",
         "帮我安排太原周边一日古建游"),
        ("会讲故事", "从斗拱榫卯讲到梁思成考察，可一键语音讲解。",
         "佛光寺为何被称为中国第一国宝"),
    ]
    st.markdown(
        '<div class="guide-row">'
        + "".join(
            f'<div class="guide-card"><div class="t">{_t}</div><div class="d">{_d}</div></div>'
            for _t, _d, _ in _GUIDES
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    _gcols = st.columns(3)
    for _col, (_t, _d, _q) in zip(_gcols, _GUIDES):
        if _col.button(_q, key=f"guide_{_t}", use_container_width=True):
            st.session_state["pending"] = _q
            st.rerun()


for i, h in enumerate(history):
    with st.chat_message(h["role"]):
        if h["role"] == "assistant" and h.get("steps"):
            with st.expander(f"🧠 智能体工作流 · {len(h['steps'])} 次工具调用"):
                for s in h["steps"]:
                    st.markdown(f"**🔧 {s['name']}** `{json.dumps(s['args'], ensure_ascii=False)}`")
                    st.caption(str(s["result"])[:400])
        st.markdown(h["content"])
        if h["role"] == "assistant" and len(h["content"]) > 10:
            if st.button("🔊 语音讲解", key=f"tts_{i}"):
                with st.spinner("合成语音中…"):
                    try:
                        p, mime = tts_file(h["content"])
                        st.audio(p, format=mime)
                    except Exception as e:  # noqa: BLE001
                        st.warning(f"语音合成失败：{e}")

# ---------------- 拍照识古建 ----------------
photo = st.session_state.pop("photo", None)
if photo is not None:
    mime = st.session_state.pop("photo_mime", "image/jpeg")
    history.append({"role": "user", "content": "📷 我上传了一张古建照片，帮我看看这是什么？"})
    with st.chat_message("user"):
        st.markdown("📷 我上传了一张古建照片，帮我看看这是什么？")
        st.image(photo, width=300)
    with st.chat_message("assistant"):
        with st.spinner("晋迹正在识别照片、比对知识库…"):
            try:
                reply, steps = agent.identify_photo(photo, level, mime)
            except Exception as e:  # noqa: BLE001
                reply, steps = f"⚠️ 识别失败：{e}", []
        if steps:
            with st.expander(f"🧠 智能体工作流 · {len(steps)} 次工具调用"):
                for s in steps:
                    st.markdown(f"**🔧 {s['name']}** `{json.dumps(s['args'], ensure_ascii=False)}`")
                    st.caption(str(s["result"])[:400])
        st.markdown(reply)
    history.append({"role": "assistant", "content": reply, "steps": steps})
    st.rerun()

# ---------------- 输入处理 ----------------
inp = st.chat_input("问问晋迹：景点讲解 / 行程规划 / 拍照机位…")
pending = st.session_state.pop("pending", None)
if inp or pending:
    text = inp or pending
    history.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.markdown(text)
    with st.chat_message("assistant"):
        with st.spinner("晋迹正在查阅资料、调用工具…"):
            try:
                reply, steps = agent.run_agent(
                    text,
                    [{"role": h["role"], "content": h["content"]} for h in history[:-1]],
                    level=level,
                )
            except Exception as e:  # noqa: BLE001
                reply, steps = f"⚠️ 出错了：{e}", []
        if steps:
            with st.expander(f"🧠 智能体工作流 · {len(steps)} 次工具调用"):
                for s in steps:
                    st.markdown(f"**🔧 {s['name']}** `{json.dumps(s['args'], ensure_ascii=False)}`")
                    st.caption(str(s["result"])[:400])
        st.markdown(reply)
    history.append({"role": "assistant", "content": reply, "steps": steps})
    st.rerun()
