"""晋迹·AI古建导览 —— 全局配置"""
import os

# DeepSeek API 密钥：优先读环境变量，其次读本地 secret.py
# ⚠️ 提交作品时不要打包 secret.py！
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    try:  # Streamlit Community Cloud：从云端 Secrets 读取
        import streamlit as st
        API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
    except Exception:
        pass
if not API_KEY:
    try:
        from secret import DEEPSEEK_API_KEY
        API_KEY = DEEPSEEK_API_KEY
    except ImportError:
        pass

API_BASE = "https://api.deepseek.com"
MODEL = os.environ.get("JINJI_MODEL", "deepseek-chat")
MAX_TOOL_LOOP = 6       # Agent 单轮最多工具调用次数
TEMPERATURE = 0.7

# 无 Key 或显式开启时进入离线演示模式（本地 mock，不调 API）
MOCK = os.environ.get("MOCK_LLM") == "1" or not API_KEY
