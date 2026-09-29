# -*- coding: utf-8 -*-
"""生成 Agent 架构图 docs/assets/agent-arch.png（PIL 绘制，古建配色）"""
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1180, 620
BG = "#FAF6EF"
INK = "#3B2F2A"
RED = "#A03A2C"
GOLD = "#C9A227"
LINE = "#8a7560"

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(sz, bold=False):
    for p in ("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
              "C:/Windows/Fonts/msyh.ttc"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def box(x1, y1, x2, y2, title, sub="", fill="#FFFDF8", outline=RED, title_bold=True):
    d.rounded_rectangle([x1, y1, x2, y2], radius=14, fill=fill, outline=outline, width=3)
    f1 = font(22, title_bold)
    d.text(((x1 + x2) / 2, (y1 + y2) / 2 - (12 if sub else 0)), title,
           font=f1, fill=INK, anchor="mm")
    if sub:
        d.text(((x1 + x2) / 2, (y1 + y2) / 2 + 22), sub, font=font(16), fill="#7a6a55", anchor="mm")


def arrow(x1, y1, x2, y2, label="", color=LINE):
    d.line([x1, y1, x2, y2], fill=color, width=3)
    # 箭头
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    for da in (math.pi * 5 / 6, -math.pi * 5 / 6):
        px = x2 - 16 * math.cos(ang + da)
        py = y2 - 16 * math.sin(ang + da)
        d.line([x2, y2, px, py], fill=color, width=3)
    if label:
        d.text(((x1 + x2) / 2, (y1 + y2) / 2 - 12), label, font=font(15), fill=color, anchor="mm")


# 标题
d.text((W / 2, 42), "晋迹 · Agent 工作流架构", font=font(30, True), fill=RED, anchor="mm")
d.text((W / 2, 78), "用户提问 → 大模型判断 → 调用工具查证 → 基于知识库作答 → 语音讲解",
       font=font(17), fill="#7a6a55", anchor="mm")

# 布局
box(60, 130, 300, 230, "👤 用户提问", "“山西最早的木构是哪座？”", outline=GOLD)
box(470, 130, 760, 230, "🧠 大模型智能体", "DeepSeek（deepseek-chat）\n判断需要什么资料 / 规划", outline=RED)

arrow(300, 180, 470, 180, "提问")

# 工具层三个盒子
box(40, 340, 280, 470, "🔧 检索工具", "search_attractions", outline=GOLD)
box(310, 340, 550, 470, "🔧 详情工具", "get_attraction_detail", outline=GOLD)
box(580, 340, 820, 470, "🔧 规划工具", "plan_itinerary", outline=GOLD)

arrow(600, 230, 440, 340, "调用工具")
arrow(640, 230, 430, 340, "", color=BG)  # 遮蔽交叉线（视觉修正）
arrow(640, 230, 700, 340, "调用工具")

# 知识库
box(880, 340, 1120, 470, "📚 本地知识库", "35 处古建 + 4 条路线\n每条约含真实来源标注", outline=GOLD)
arrow(820, 405, 880, 405, "")

# 工具结果回流
arrow(160, 470, 530, 545, "真实资料")
arrow(690, 470, 620, 545, "真实资料")

# 组织讲解
box(560, 520, 900, 600, "🗣 基于知识库组织讲解", "不编造 · 可注明来源", outline=RED)
arrow(760, 230, 730, 520, "", color=LINE)

# 语音
box(950, 520, 1140, 600, "🔊 语音讲解", "edge-tts 合成", outline=GOLD)
arrow(900, 560, 950, 560, "")

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "docs", "assets", "agent-arch.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
img.save(out)
print("架构图已生成:", out)
