"""晋迹 · Agent 核心：DeepSeek 函数调用循环（检索 → 规划 → 讲解）"""
import json
import urllib.request

import config
import kb

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_attractions",
            "description": "根据目的地/城市/主题检索山西古建知识库，返回景点清单与简介",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索词，如'晋北'、'大同'、'黑神话取景地'、'唐代木构'、'应县木塔'"},
                    "top_k": {"type": "integer", "description": "返回条数，默认3"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_attraction_detail",
            "description": "查询某个具体景点的详细资料（年代、看点、贴士等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "景点名称，如'佛光寺'、'应县木塔'"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_itinerary",
            "description": "按天数、城市、兴趣主题生成山西古建行程规划草案",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "游玩天数，1-5"},
                    "city": {"type": "string", "description": "想去的城市或区域，如'晋北'、'太原'、'大同'，可留空"},
                    "interests": {"type": "string", "description": "兴趣主题，如'黑神话取景地'、'唐代木构'、'晋商大院'，可留空"},
                },
                "required": ["days"],
            },
        },
    },
]

LEVEL_PROMPTS = {
    "basic": """你是「晋迹」，一名深耕山西古建的AI导览智能体，服务来山西的游客与古建爱好者。
工作守则：
1. 涉及景点知识时，先调用 search_attractions 或 get_attraction_detail 工具检索知识库，再基于资料作答；知识库没有的信息要明确说明，不得编造年代、数据；讲解重要结论时可注明来源（如"据全国重点文物保护单位名录"）。
2. 涉及行程规划时，调用 plan_itinerary 工具生成路线草案，再润色成可读行程（保留每天景点节奏，可补充吃住行小贴士）。
3. 回答控制在350字以内，多用小标题和列表；语气专业又亲切，像一位懂行的导游朋友，可适当讲梁思成、林徽因、黑神话悟空等文化故事。
4. 与山西古建无关的问题，礼貌引导回导览主题。""",
    "pro": """你是「晋迹」，面向懂些门道的古建爱好者的AI导览智能体。
工作守则：
1. 先调用 search_attractions / get_attraction_detail 检索知识库再作答，不编造；重要结论注明来源。
2. 讲解适度使用建筑术语（斗拱、铺作、歇山、庑殿、副阶周匝、双套筒等），每个术语后配一句通俗解释，让内行点头、外行听懂。
3. 优先利用工具返回的「建筑形制」字段，指出可现场观察的结构特征。
4. 回答≤350字，小标题列表，像一位懂行的导游朋友。""",
    "hardcore": """你是「晋迹」，面向硬核古建爱好者的断代级导览智能体。
工作守则：
1. 先调用 search_attractions / get_attraction_detail 检索知识库再作答，不编造；重要结论注明来源。
2. 使用专业术语（铺作/材分/梭柱/侧脚/生起/推山/收山等）讲解；必须给出该建筑的断代依据：年代题记、结构特征、风格比较。
3. 工具返回的「建筑形制」「断代依据」「冷知识与争议」字段必须充分利用，争议与冷知识单独成段。
4. 回答≤400字，像一位古建断代专家在带你逐构件读古建。""",
    "planner": """你是「晋迹」的「晋北古建深度导览规划师」——一位深耕山西古建十余年的资深导游与建筑史学者，热情、严谨、幽默，善于用生活化比喻拆解复杂结构。

工作守则：
1. 涉及行程规划，先调用 plan_itinerary 工具生成路线草案（晋北、大同、应县、浑源、佛光寺、南禅寺、悬空寺等点），再基于草案润色成可执行的详细攻略。
2. 涉及景点知识，先调用 search_attractions 或 get_attraction_detail 检索知识库再作答；知识库没有的信息（实时门票价格、预约方式、营业时间等）须说明"以官方最新为准"，绝不编造。
3. 每个景点至少点出1个具体建筑构件或结构特征（如斗拱铺作、梁架、柱础、飞梁），并给出肉眼观察方法；所有术语必须搭配"搭积木/撑伞/跷跷板"这类生活化比喻，让小白听懂。
4. 拒绝"值得一看""很美"等空话，只给可操作的观察点与冷知识。
5. 行程精确：时间轴须含车程、游览时长、用餐与休息节点；用 Markdown 排版（标题、每日时间轴、【看点拆解】【实操贴士】板块）；补门票预约（尤其悬空寺限流抢票）、食宿推荐（老字号类型举例，不推商业品牌）、避坑指南。
6. 加入1-2个学术争议或冷知识，用大白话讲成侦探故事。
7. 结尾以具体、有吸引力的互动提问收束，避免生硬追问。
8. 语气自然流露对古建的热爱但不过度抒情；与晋北古建无关的问题礼貌引导回主题。
9. 篇幅：行程规划类回答可详细展开（时间轴+看点拆解+实操贴士+冷知识俱全），控制在 800 字以内；单个景点的讲解则简洁些，约 300 字，信息密集不灌水。""",
}


def _chat(messages, tools=None):
    """调用 DeepSeek（OpenAI 兼容接口），或离线 mock 模式"""
    if config.MOCK:
        return _mock_chat(messages)
    body = {
        "model": config.MODEL,
        "messages": messages,
        "temperature": config.TEMPERATURE,
        "stream": False,
    }
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(
        config.API_BASE + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config.API_KEY,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"API 调用失败（HTTP {e.code}）：{msg[:200]}")
    except Exception as e:
        raise RuntimeError(f"网络异常：{e}")


def _mock_chat(messages):
    """离线演示模式：不依赖网络与密钥，走一轮固定工具调用，用于开发与断网演示"""
    last = messages[-1]
    if last["role"] == "user":
        q = last["content"]
        if any(w in q for w in ("规划", "行程", "路线", "几日", "几天")):
            args = {"days": 2, "city": "晋北", "interests": "古建"}
            return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
                {"id": "mock_plan", "type": "function",
                 "function": {"name": "plan_itinerary", "arguments": json.dumps(args, ensure_ascii=False)}}]}}]}
        return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
            {"id": "mock_search", "type": "function",
             "function": {"name": "search_attractions",
                          "arguments": json.dumps({"query": q}, ensure_ascii=False)}}]}}]}
    return {"choices": [{"message": {"role": "assistant", "content":
        "（离线演示模式）山西现存古建筑约 2.8 万处，其中元代及以前木构建筑 509 处，是全国同类建筑最集中的省份。"
        "从唐代南禅寺、佛光寺，到辽代应县木塔，再到金代崇福寺——三晋大地堪称'中国古建筑博物馆'。"
        "正式使用时接入 DeepSeek 大模型，可获得基于知识库检索的完整讲解。"}}]}


def _fmt(a, level="basic"):
    a = kb.with_source(kb.with_hardcore(a, level))
    out = {"名称": a["name"], "城市": a["city"], "年代": a["era"],
           "标签": a["tags"], "简介": a["summary"], "看点": a["highlights"], "贴士": a["tips"],
           "来源": a["source"]}
    if "arch" in a:
        out["建筑形制"] = a["arch"]
    if "dating" in a:
        out["断代依据"] = a["dating"]
    if "debate" in a:
        out["冷知识与争议"] = a["debate"]
    return out


def _exec_search(args, level="basic"):
    q = str(args.get("query", "")).strip()
    top_k = int(args.get("top_k", 3) or 3)
    hits = kb.retrieve(q, top_k=min(max(top_k, 1), 10))   # 上限提到 10：主题类问题（黑神话取景地共 9 处）可一次取全
    if not hits:
        return {"命中": 0, "提示": "知识库暂无匹配，请换关键词（景点名/城市/主题）"}
    return {"命中": len(hits), "景点": [_fmt(a, level) for a in hits]}


def _exec_detail(args, level="basic"):
    name = str(args.get("name", "")).strip()
    a = kb.find_attraction(name)
    if not a:
        return {"命中": 0, "提示": f"未找到「{name}」，可先调用 search_attractions 检索"}
    return _fmt(a, level)


def _exec_plan(args, level="basic"):
    days = int(args.get("days", 2) or 2)
    city = str(args.get("city", "") or "").strip()
    interests = str(args.get("interests", "") or "").strip()
    q = city + interests

    # 0) 断代主题路线（按朝代演变编排）—— 必须尊重用户给的天数
    if any(w in q for w in ("断代", "朝代", "演变", "千年")):
        dyn = next((r for r in kb.ROUTES if "断代" in r["name"]), None)
        if dyn is not None:
            _pd = dyn["days"]
            if days < _pd:                     # 用户天数少于预设 → 截取前段，而不是硬返回整条
                return {"推荐路线": f"{dyn['name']}（截取前 {days} 日）", "天数": days,
                        "覆盖城市": dyn["cities"], "行程": dyn["itinerary"][:days],
                        "说明": f"断代主题路线完整为 {_pd} 日，已按你要求的 {days} 日截取前段；"
                                f"若想走完整演变线，可以改成 {_pd} 日"}
            return {"推荐路线": dyn["name"], "天数": _pd, "覆盖城市": dyn["cities"],
                    "行程": dyn["itinerary"],
                    "说明": "断代主题路线（按朝代演变编排，每节点附形制特征），请大模型据此讲解断代逻辑"}

    # 1) 精选预设路线优先（同天数 + 主题/城市命中）
    preset = None
    if any(w in q for w in ("黑神话", "取景", "悟空")):
        preset = next((r for r in kb.ROUTES if r["days"] == days and "黑神话" in r["name"]), None)
    if preset is None:
        preset = next((r for r in kb.ROUTES
                       if r["days"] == days and city and city in r["name"]), None)
    if preset is None and len(q) >= 2:
        preset = next((r for r in kb.ROUTES
                       if r["days"] == days and any(w in r["name"] for w in q)), None)
    if preset is not None:
        return {"推荐路线": preset["name"], "天数": preset["days"], "覆盖城市": preset["cities"],
                "行程": preset["itinerary"], "说明": "精选路线（人工审定），请大模型据此润色讲解"}

    # 2) 动态编排（覆盖任意城市/主题组合，如运城、晋东南、大院主题等）
    return kb.build_itinerary(days, city, interests)


EXECUTORS = {
    "search_attractions": _exec_search,
    "get_attraction_detail": _exec_detail,
    "plan_itinerary": _exec_plan,
}


def run_agent(user_msg, history, level="basic"):
    """执行一轮 Agent 循环。
    history: [{"role": "user"/"assistant", "content": str}, ...]
    level: basic / pro / hardcore / planner 导览模式分层
    返回 (assistant_text, steps)，steps 为工具调用记录列表。"""
    messages = [{"role": "system", "content": LEVEL_PROMPTS.get(level, LEVEL_PROMPTS["basic"])}]
    for h in history[-8:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    steps = []
    # 程序级「先查再答」约束：命中知识库的问题，若模型一次工具都没调用就想直接作答，
    # 由程序强制补一轮检索（不依赖模型自觉）；最多强制一次，避免死循环。
    _need_source = bool(kb.retrieve(user_msg, top_k=1))
    _enforced = False
    for _ in range(config.MAX_TOOL_LOOP):
        resp = _chat(messages, tools=TOOLS)
        msg = resp["choices"][0]["message"]
        if msg.get("tool_calls"):
            messages.append({"role": "assistant", "content": msg.get("content"),
                             "tool_calls": msg["tool_calls"]})
            for tc in msg["tool_calls"]:
                fn = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                if fn in EXECUTORS:
                    result = EXECUTORS[fn](args, level)
                else:
                    result = {"错误": f"未知工具 {fn}"}
                steps.append({"name": fn, "args": args, "result": result})
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": json.dumps(result, ensure_ascii=False)})
            continue
        if _need_source and not steps and not _enforced:
            _enforced = True
            messages.append({"role": "assistant", "content": msg.get("content") or ""})
            messages.append({"role": "system", "content":
                "（系统检查）你刚才没有调用任何工具就直接作答了。请先调用 search_attractions 或 "
                "get_attraction_detail 检索本地知识库，再基于检索到的资料作答；"
                "若检索无结果，请如实说明知识库未收录，不要凭记忆编造年代与数据。"})
            continue
        return (msg.get("content") or "（晋迹思考了一下，没有输出内容，请再问一次～）"), steps
    return "抱歉，我在思考时有点卡住了，请换个问法试试～", steps


VISION_PROMPT = """你是一名古建筑鉴定助手。看这张照片，只输出 JSON（不要多余文字）：
{"建筑类型": "木塔/佛殿/石窟/彩塑/楼阁/其他", "形制特征": "一句话描述结构与形制（斗拱铺作、屋顶形式、层数、用材等）", "可能年代": "可判断则写朝代，否则写'无法判断'", "检索词": "3-6个关键词，用顿号分隔"}"""


def identify_photo(image_bytes, level="basic", mime="image/jpeg"):
    """拍照识古建：视觉特征提取 → 关键词检索知识库 → 基于资料讲解。
    返回 (reply, steps)。离线模式返回提示。"""
    import base64
    if config.MOCK:
        return ("（离线演示模式暂不支持拍照识别，配置 API Key 后即可使用）", [])
    b64 = base64.b64encode(image_bytes).decode()
    resp = _chat([{"role": "user", "content": [
        {"type": "text", "text": VISION_PROMPT},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64," + b64}}]}])
    desc = (resp["choices"][0]["message"].get("content") or "").strip()
    steps = [{"name": "identify_photo", "args": {"图像": "用户上传照片"},
              "result": (desc or "视觉模型未返回内容")[:300]}]

    # 解析视觉模型给出的检索词
    try:
        info = json.loads(desc[desc.find("{"): desc.rfind("}") + 1])
    except Exception:  # noqa: BLE001
        info = {}
    kw = str(info.get("检索词", "") or "")
    hits = kb.retrieve(kw if kw else desc, top_k=3)
    if not hits:
        hits = kb.retrieve(desc, top_k=2)

    sysp = LEVEL_PROMPTS.get(level, LEVEL_PROMPTS["basic"])
    kbfmt = json.dumps([_fmt(a, level) for a in hits], ensure_ascii=False)
    user = (f"用户上传了一张古建照片。视觉模型识别结果：{desc}\n"
            f"知识库匹配到的条目（可能相关）：{kbfmt}\n"
            "请讲解：这是什么古建、有哪些可观察的特征、为什么这样判断；"
            "若匹配不充分，就如实描述所见特征并建议用户用文字继续提问。回答≤350字。")
    resp2 = _chat([{"role": "system", "content": sysp}, {"role": "user", "content": user}])
    reply = (resp2["choices"][0]["message"].get("content") or "（识别完成，但没有生成讲解，请再试一次）")
    return reply, steps
