# 🏯 晋迹 —— 山西古建智能导览体

华北五省大学生计算机应用大赛 · 大模型与智能体应用赛道参赛作品。

面向文旅垂直场景的工具调用型大模型智能体：
本地山西古建知识库（35 处古建 + 5 条精选路线 + 任意城市动态编排）＋ DeepSeek 大模型函数调用，
实现「检索 → 规划 → 讲解」的 Agent 工作流，支持语音讲解。

**技术栈（版本号）**：Windows 11 · Python 3.14 · Streamlit 1.64.0 · edge-tts 7.2.8 ·
DeepSeek（deepseek-chat，官方 API）—— 全程国产大模型，响应大赛国产化导向。

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖（国内可用清华镜像）
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2. 配置 API Key
copy secret_example.py secret.py   # 编辑 secret.py 填入你的 DeepSeek Key

# 3. 启动
.venv\Scripts\python -m streamlit run app.py
```

- 未配置 Key 时自动进入「离线演示模式」（本地 mock，可演示完整 Agent 流程）
- 配置 Key 后使用 `deepseek-chat` 模型（`JINJI_MODEL` 环境变量可改模型名）
- ⚠️ 改动代码后需**重启应用**才生效（关掉 bat 窗口重新双击，或按 Ctrl+C 重启 streamlit）

## 目录结构

| 文件 | 说明 |
|---|---|
| app.py | Streamlit 前端（聊天界面 + 智能体工作流可视化 + 语音） |
| agent.py | Agent 核心：DeepSeek 函数调用循环（3 个工具） |
| kb.py | 山西古建知识库（35 处）+ 检索 + 精选路线 + 动态行程编排 |
| config.py | 配置（API Key / 模型 / 循环上限） |
| secret_example.py | 密钥模板（secret.py 不参与提交） |

## 打包提交清单

1. 源码 zip：`app.py / agent.py / kb.py / config.py / requirements.txt / README.md / secret_example.py`
   （⚠️ 不要打包 secret.py、.venv、__pycache__）
2. 运行说明：见上「快速开始」
3. 演示视频：录屏软件录制浏览器界面（建议 3-5 分钟，含 Agent 工具调用过程）

## AI 使用声明（提交时按官方要求填写）

本作品开发过程中使用了 AI 辅助编程工具：代码骨架与知识库文案由大模型辅助生成，
经过人工审校与测试；Agent 工作流设计、工具定义、知识库检索策略与界面设计为原创设计。
