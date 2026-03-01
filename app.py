"""
Idea 需求分析器（开源版）
流式输出 · 三栏布局 · 双模式（产品需求 / 文学创作）· 13模块PRD · 竞品分析 · AI开发Prompt · 测试用例
数据存储在浏览器 Session，不写服务器文件。
"""

import json
import re
import time
import uuid
from datetime import datetime

import httpx
import openai
import streamlit as st

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Idea 需求分析器",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Sidebar: API 配置 ────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ API 配置")
    st.caption("支持任何 OpenAI 兼容格式的 API")

    cfg_base = st.text_input(
        "API 请求地址",
        value=st.session_state.get("cfg_base", "https://ark.cn-beijing.volces.com/api/v3"),
        placeholder="https://api.openai.com/v1",
        help="填写你的 API Endpoint，需兼容 OpenAI Chat Completions 格式",
    )
    cfg_key = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.get("cfg_key", ""),
        placeholder="sk-xxx",
    )
    cfg_model = st.text_input(
        "模型名称",
        value=st.session_state.get("cfg_model", "doubao-seed-2-0-pro-260215"),
        help="填写对应平台的模型 ID，如 gpt-4o、doubao-seed-2-0-pro-260215 等",
    )
    cfg_websearch = st.checkbox(
        "启用联网搜索（仅火山引擎 Ark 平台支持）",
        value=st.session_state.get("cfg_websearch", False),
        help="竞品分析时联网搜索，需在火山引擎控制台开通「联网内容插件」",
    )

    if cfg_base:
        st.session_state.cfg_base      = cfg_base
    if cfg_key:
        st.session_state.cfg_key       = cfg_key
    if cfg_model:
        st.session_state.cfg_model     = cfg_model
    st.session_state.cfg_websearch = cfg_websearch

    if cfg_key and cfg_base:
        st.success("✅ 配置完成，可以开始使用")
    else:
        st.warning("⚠️ 请填写 API 地址和 Key")

    st.markdown("---")
    st.caption("💡 数据仅保存在当前浏览器 Session，刷新页面后清空")
    st.caption("[📖 使用说明 & 源码](https://github.com/0000-huajiao/idea-analyzer)")


def is_configured() -> bool:
    return bool(st.session_state.get("cfg_key") and st.session_state.get("cfg_base"))


# ─── Constants ────────────────────────────────────────────────────────────────
MAX_RETRY     = 3
HISTORY_LIMIT = 20

# ─── PRD module definitions (产品模式) ────────────────────────────────────────
PRD_MODULES = [
    ("doc_info",          "文档基础信息"),
    ("background",        "需求背景与目标"),
    ("scope",             "需求范围"),
    ("user_roles",        "用户角色与使用场景"),
    ("functional_req",    "功能需求"),
    ("non_functional",    "非功能需求"),
    ("business_rules",    "业务规则与逻辑"),
    ("ui_prototype",      "页面原型与交互说明"),
    ("ui_style",          "页面风格与配色"),
    ("data_requirements", "数据需求"),
    ("dependencies",      "接口与依赖说明"),
    ("testing",           "测试要点与验收标准"),
    ("launch_plan",       "上线计划与风险"),
    ("appendix",          "附录"),
]

LIST_FIELDS    = {"user_roles", "business_rules", "testing"}
FEATURE_FIELDS = {"functional_req"}

EXPORT_HINTS = {
    "doc_info":          "- 文档名称：\n- 版本号：v1.0\n- 更新日期：\n- 适用平台：\n- 阅读对象：产品/开发/测试\n- 变更记录：首次创建",
    "background":        "- 为什么要做：\n- 解决什么问题：\n- 业务目标：\n- 用户目标：\n- 预期收益：",
    "scope":             "**本期包含：**\n\n**不包含（边界）：**\n\n**下期规划：**",
    "user_roles":        ["（待填写）角色：使用场景和典型流程"],
    "functional_req":    [{"module": "（待填写）", "desc": "", "entry": "", "interaction": "",
                           "fields": "", "actions": "", "error_handling": "", "permissions": ""}],
    "non_functional":    "- 性能要求：\n- 兼容性：\n- 安全性：\n- 易用性：",
    "business_rules":    ["（待填写）规则描述"],
    "ui_prototype":      "- 页面跳转关系：\n- 动效/弹窗说明：\n- 文案规范：",
    "ui_style":          "- 整体风格：（如：极简清爽 / 活泼年轻 / 商务专业 / 科技感）\n- 主色调：\n- 辅助色：\n- 字体方向：\n- 特殊视觉要求：",
    "data_requirements": "- 埋点事件：\n- 统计指标：\n- 数据口径：",
    "dependencies":      "- 第三方服务：\n- 接口约定：\n- 依赖系统：",
    "testing":           ["（待填写）测试场景：验收条件"],
    "launch_plan":       "- 排期/里程碑：\n- 依赖资源：\n- 风险及预案：",
    "appendix":          "**名词解释：**\n\n**参考资料：**\n\n**Q&A：**",
}

# ─── 三阶段引导系统（产品模式）────────────────────────────────────────────────
def field_filled(prd: dict, key: str) -> bool:
    val = prd.get(key)
    return len(val) > 0 if isinstance(val, list) else bool(val)

GUIDED_STAGES = [
    {
        "id": 1, "emoji": "🎯", "title": "说清楚是什么",
        "desc": "产品定位 · 解决的问题 · 核心目标",
        "check": lambda prd, pct: pct >= 25 and field_filled(prd, "background"),
        "prompt": (
            "【当前引导阶段：第1阶段——说清楚是什么】\n"
            "请用2-3个简单问题聚焦了解：这个产品是什么？解决什么问题？目标是什么？\n"
            "本阶段完成后 completeness 设为 25-40。"
        ),
    },
    {
        "id": 2, "emoji": "👥", "title": "搞清楚给谁用",
        "desc": "目标用户 · 使用场景 · 典型流程",
        "check": lambda prd, pct: pct >= 45 and field_filled(prd, "user_roles"),
        "prompt": (
            "【当前引导阶段：第2阶段——搞清楚给谁用】\n"
            "请用2-3个简单问题聚焦了解：谁会用？什么场景下用？怎么用？\n"
            "本阶段完成后 completeness 设为 45-60。"
        ),
    },
    {
        "id": 3, "emoji": "⚡", "title": "想清楚怎么做",
        "desc": "核心功能 · 需求范围 · 用户流程",
        "check": lambda prd, pct: pct >= 65 and field_filled(prd, "functional_req"),
        "prompt": (
            "【当前引导阶段：第3阶段——想清楚怎么做】\n"
            "请用3-4个简单问题聚焦了解：核心功能有哪些？范围边界是什么？用户怎么一步步操作？\n"
            "本阶段完成后 completeness 设为 65-75。"
        ),
    },
]

def get_completed_stages(idea: dict) -> list[int]:
    prd = idea.get("prd", {})
    pct = idea.get("completeness", 0)
    return [s["id"] for s in GUIDED_STAGES if s["check"](prd, pct)]

def get_current_guided_stage(idea: dict) -> int:
    completed = get_completed_stages(idea)
    for s in GUIDED_STAGES:
        if s["id"] not in completed:
            return s["id"]
    return 4

def get_stage_prompt(idea: dict) -> str:
    sid = get_current_guided_stage(idea)
    if sid <= 3:
        return GUIDED_STAGES[sid - 1]["prompt"]
    return "【深化阶段】前三阶段已完成！请继续深化：非功能需求、业务规则、上线计划等。completeness 可设为 75-100。"

# ─── 五阶段引导系统（文学模式）────────────────────────────────────────────────
def lit_field_filled(outline: dict, key: str) -> bool:
    val = outline.get(key)
    if isinstance(val, (list, dict)):
        return len(val) > 0
    return bool(val)

LIT_STAGES = [
    {
        "id": 1, "emoji": "🌍", "title": "背景设定",
        "desc": "世界观 · 故事类型 · 基调风格",
        "check": lambda o, pct: pct >= 20 and (lit_field_filled(o, "world") or lit_field_filled(o, "genre")),
        "prompt": (
            "【当前引导阶段：第1阶段——背景设定】\n"
            "请用2-3个问题了解：这是什么类型的故事？发生在什么背景下？整体风格基调是什么？\n"
            "本阶段完成后 completeness 设为 20-35。"
        ),
    },
    {
        "id": 2, "emoji": "👤", "title": "人物塑造",
        "desc": "主角 · 配角 · 人物弧光",
        "check": lambda o, pct: pct >= 40 and lit_field_filled(o, "characters"),
        "prompt": (
            "【当前引导阶段：第2阶段——人物塑造】\n"
            "请用2-3个问题了解：主角是谁？有什么性格特点？会经历什么成长或变化？有哪些重要配角？\n"
            "本阶段完成后 completeness 设为 40-55。"
        ),
    },
    {
        "id": 3, "emoji": "⚡", "title": "冲突结构",
        "desc": "核心冲突 · 故事结构 · 情节起伏",
        "check": lambda o, pct: pct >= 60 and lit_field_filled(o, "conflict") and lit_field_filled(o, "plot"),
        "prompt": (
            "【当前引导阶段：第3阶段——冲突结构】\n"
            "请用3-4个问题了解：主角面临的最大阻碍是什么？故事怎么开始？高潮在哪里？结局走向如何？\n"
            "本阶段完成后 completeness 设为 60-75。"
        ),
    },
    {
        "id": 4, "emoji": "🗺️", "title": "写作计划",
        "desc": "叙事视角 · 切入点 · 章节节奏",
        "check": lambda o, pct: pct >= 75 and lit_field_filled(o, "writing_plan"),
        "prompt": (
            "【当前引导阶段：第4阶段——写作计划】\n"
            "请用2-3个问题了解：从哪个角色的视角写？以什么事件作为开篇切入点？前几章大致怎么安排？\n"
            "本阶段完成后 completeness 设为 75-85。"
        ),
    },
    {
        "id": 5, "emoji": "📚", "title": "参考资料",
        "desc": "同类作品 · 创作灵感来源",
        "check": lambda o, pct: pct >= 85 and lit_field_filled(o, "references"),
        "prompt": (
            "【当前引导阶段：第5阶段——参考资料】\n"
            "推荐几部和这个故事风格、类型相近的作品，说明可以参考的地方。completeness 可设为 85-100。"
        ),
    },
]

def get_lit_completed_stages(idea: dict) -> list[int]:
    outline = idea.get("outline", {})
    pct     = idea.get("completeness", 0)
    return [s["id"] for s in LIT_STAGES if s["check"](outline, pct)]

def get_lit_current_stage(idea: dict) -> int:
    completed = get_lit_completed_stages(idea)
    for s in LIT_STAGES:
        if s["id"] not in completed:
            return s["id"]
    return len(LIT_STAGES) + 1

def get_lit_stage_prompt(idea: dict) -> str:
    sid = get_lit_current_stage(idea)
    if sid <= len(LIT_STAGES):
        return LIT_STAGES[sid - 1]["prompt"]
    return "【深化阶段】所有阶段已完成！请继续丰富细节，completeness 可设为 90-100。"

# ─── System prompts ───────────────────────────────────────────────────────────
MAIN_PROMPT = """你是一位资深产品经理，专门帮助非专业用户用大白话梳理产品需求。

【提问规则】
- 每次只问一个问题，语言通俗，绝对不用行业术语
- 用户说"不知道"或"跳过"时，根据常识填入合理默认值，继续推进
- 严格按照系统提示中的【当前引导阶段】聚焦提问，不要跳跃
- completeness ≥ 85 时将 question 设为 null
- 每次回复都要尽量填充所有已知的PRD字段
- ui_style 为空时，在核心功能已明确后询问："你对这个产品的视觉风格有什么想法吗？比如极简清爽、活泼年轻、商务专业……没想法的话我来帮你设计一套 😊"；用户没有想法或跳过时，根据产品定位自行设计一套合适的风格与配色方案填入

【只输出合法 JSON，不含任何其他文字】
{
  "analysis": "对用户回答的简短友好反馈（1-2句）",
  "question": "下一个通俗问题，或 null",
  "question_category": "问题类别",
  "prd": {
    "doc_info":          "适用项目、平台、阅读对象等基本信息",
    "background":        "需求背景、为什么做、目标、预期收益",
    "scope":             "包含哪些功能；不包含哪些（边界）；本期/下期划分",
    "user_roles":        ["角色名：使用场景和典型流程"],
    "functional_req":    [{"module":"模块名","desc":"功能说明","entry":"入口","interaction":"交互逻辑","fields":"字段说明","actions":"操作行为","error_handling":"异常处理","permissions":"权限控制"}],
    "non_functional":    "性能、兼容性、安全性、易用性",
    "business_rules":    ["规则：状态流转/计算公式/校验规则"],
    "ui_prototype":      "页面跳转、动效弹窗、文案规范",
    "ui_style":          "整体风格 / 主色调 / 辅助色 / 字体方向 / 特殊视觉要求（用户无想法时由AI根据产品定位设计）",
    "data_requirements": "埋点事件、统计指标、数据口径",
    "dependencies":      "第三方服务、接口约定、依赖系统",
    "testing":           ["测试场景：验收条件"],
    "launch_plan":       "排期里程碑、依赖资源、风险预案",
    "appendix":          "名词解释、参考资料、Q&A"
  },
  "flowchart": "Mermaid flowchart TD 代码，节点标签必须用双引号",
  "completeness": 整数0到100
}

【Mermaid 格式示例】
flowchart TD
    A(["开始"]) --> B["打开App"]
    B --> C{"已登录?"}
    C -->|"否"| D["注册登录"]
    C -->|"是"| E["主界面"]
    D --> E --> F["核心操作"] --> G(["完成"])
"""

LIT_PROMPT = """你是一位经验丰富的故事编辑和创作顾问，专门帮助创作者梳理故事框架。

【提问规则】
- 每次只问一个问题，语言自然亲切，像朋友聊天一样
- 问题覆盖顺序：故事类型/背景设定 → 核心人物 → 主要冲突 → 故事主线 → 叙事视角与切入点 → 章节节奏
- 用户说"不知道"或"跳过"时，根据常见创作规律给出合理默认值，继续推进
- completeness ≥ 85 时将 question 设为 null

【只输出合法 JSON，不含任何其他文字】
{
  "analysis": "对用户回答的简短友好反馈（1-2句，像编辑和作者在聊天）",
  "question": "下一个问题，或 null",
  "question_category": "问题类别（如：背景设定/人物塑造/剧情结构等）",
  "outline": {
    "logline": "一句话故事核心（主角 + 目标 + 障碍）",
    "genre": "故事类型与风格基调",
    "world": "世界观与背景设定",
    "characters": [
      {
        "name": "人物名",
        "role": "在故事中的角色定位",
        "personality": "性格特征",
        "arc": "人物在故事中经历的变化（人物弧光）"
      }
    ],
    "conflict": "核心冲突（主角面临的最大阻碍是什么）",
    "plot": {
      "opening": "开篇事件（用什么钩住读者）",
      "rising": "发展阶段（矛盾如何升级）",
      "climax": "高潮转折点",
      "resolution": "结局走向"
    },
    "writing_plan": {
      "perspective": "叙事视角（第一人称/第三人称/多视角）",
      "entry_character": "从哪个角色的视角开始写",
      "entry_event": "以什么事件作为切入点",
      "chapter_rhythm": "章节节奏建议（如：前三章的大致内容安排）"
    },
    "references": [
      "推荐参考的同类作品或资料（注明相似之处）"
    ]
  },
  "completeness": 整数0到100
}"""

COMPETITOR_PROMPT = """你是一位市场研究专家。根据产品PRD分析竞品（如启用联网则基于实时搜索，否则基于训练知识）。

只输出合法 JSON：
{
  "summary": "市场概况（2-3句）",
  "competitors": [{"name":"竞品名","description":"一句话描述","strengths":["优势"],"weaknesses":["劣势"],"url":"官网或空字符串"}],
  "market_gap": "市场空白和机会点",
  "differentiation": "差异化建议",
  "feasibility": {"score": 1到10整数, "rationale": "可行性理由", "recommendations": ["行动建议"]}
}"""

WIREFRAME_PROMPT = """你是一位UI/UX设计师，根据PRD（含页面风格与配色）为每个核心页面生成ASCII线框图原型。

要求：
- 用 +--+  |  [ ]  ( )  等ASCII字符表示UI元素（导航栏、按钮、输入框、卡片、列表、图片占位符等）
- 每个核心页面独立输出，标注页面名称
- 在线框图下方用1-2句说明该页面的核心交互逻辑
- 结合 ui_style 中的风格和配色，在备注里标注建议色值/风格要点
- 输出所有核心页面，不要遗漏主流程中的关键页面

只输出线框图文本，不含JSON，格式清晰易读。"""

TEST_CASE_PROMPT = """你是QA工程师。根据PRD生成测试用例。
只输出合法 JSON：
{
  "test_groups": [{"module":"模块名","cases":[{"id":"TC001","scenario":"场景","preconditions":"前置","steps":["步骤"],"expected":"预期结果","priority":"高/中/低"}]}],
  "summary": "测试要点总结"
}"""

# ─── API helpers ──────────────────────────────────────────────────────────────
def get_client() -> openai.OpenAI:
    return openai.OpenAI(
        base_url=st.session_state.get("cfg_base", ""),
        api_key=st.session_state.get("cfg_key", ""),
    )

def get_model() -> str:
    return st.session_state.get("cfg_model", "gpt-4o")

def call_api(messages: list) -> str:
    client   = get_client()
    last_err = None
    for attempt in range(MAX_RETRY):
        try:
            resp = client.chat.completions.create(
                model=get_model(), max_tokens=4096, messages=messages,
            )
            return resp.choices[0].message.content or ""
        except openai.RateLimitError as e:
            last_err = e
            if attempt < MAX_RETRY - 1:
                time.sleep(2 ** (attempt + 1))
        except openai.APIError as e:
            last_err = e
            if attempt < MAX_RETRY - 1:
                time.sleep(2 ** attempt)
    raise last_err or RuntimeError("API 调用失败")

def call_api_streaming(messages: list):
    client = get_client()
    stream = client.chat.completions.create(
        model=get_model(), max_tokens=4096, messages=messages, stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta

def call_responses_api(instructions: str, user_input: str) -> str:
    """Ark Responses API（联网搜索），仅火山引擎平台支持。"""
    url     = f"{st.session_state.get('cfg_base', '')}/responses".replace("//responses", "/responses")
    headers = {
        "Authorization": f"Bearer {st.session_state.get('cfg_key', '')}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": get_model(),
        "instructions": instructions,
        "input": user_input,
        "tools": [{"type": "web_search", "limit": 10}],
    }
    last_err = None
    for attempt in range(MAX_RETRY):
        try:
            with httpx.Client(timeout=90.0) as client:
                r = client.post(url, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            return content.get("text", "")
            return ""
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRY - 1:
                time.sleep(2 ** attempt)
    raise last_err or RuntimeError("Responses API 调用失败")

# ─── JSON / Mermaid helpers ───────────────────────────────────────────────────
def extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    depth, start = 0, -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = -1
    return {}

def sanitize_mermaid(code: str) -> str:
    def q(m: re.Match) -> str:
        lbl = m.group(1)
        return m.group(0) if lbl.startswith(('"', "'")) else f'|"{lbl}"|'
    return re.sub(r"\|([^|\"'<>\n]+)\|", q, code)

def render_mermaid(code: str, height: int = 430):
    code = re.sub(r"```[a-z]*\n?", "", code).strip()  # 剥掉 AI 可能附带的代码围栏
    code = sanitize_mermaid(code)
    if not code:
        return
    uid     = abs(hash(code)) % 99999
    code_js = json.dumps(code)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{{margin:0;padding:6px;background:#fff;}}#err{{color:#c00;font-size:12px;}}svg{{max-width:100%;height:auto;}}</style>
</head><body><div id="g{uid}"></div><div id="err"></div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"
  onload="go()" onerror="document.getElementById('err').textContent='CDN加载失败'"></script>
<script>
async function go(){{
  mermaid.initialize({{startOnLoad:false,theme:'default',securityLevel:'loose'}});
  try{{const{{svg}}=await mermaid.render('mg{uid}',{code_js});document.getElementById('g{uid}').innerHTML=svg;}}
  catch(e){{document.getElementById('err').textContent='语法错误: '+e.message;}}
}}
</script></body></html>"""
    st.components.v1.html(html, height=height, scrolling=True)
    with st.expander("📋 Mermaid 源码（可复制到 mermaid.live 预览）"):
        st.code(code, language="text")

# ─── Session-based idea storage ───────────────────────────────────────────────
def ss_ideas() -> dict:
    if "ideas" not in st.session_state:
        st.session_state.ideas = {}
    return st.session_state.ideas

def list_ideas() -> list[dict]:
    return sorted(
        [{"id": v["id"], "title": v.get("title", "未命名"),
          "updated_at": v.get("updated_at", ""), "completeness": v.get("completeness", 0),
          "idea_type": v.get("idea_type", "product")}
         for v in ss_ideas().values()],
        key=lambda x: x["updated_at"], reverse=True,
    )

def load_idea(idea_id: str) -> dict | None:
    return ss_ideas().get(idea_id)

def save_idea(idea: dict):
    idea["updated_at"] = datetime.now().isoformat()
    ss_ideas()[idea["id"]] = idea

def delete_idea(idea_id: str):
    ss_ideas().pop(idea_id, None)

def empty_prd() -> dict:
    return {k: ([] if k in LIST_FIELDS | FEATURE_FIELDS else "") for k, _ in PRD_MODULES}

def new_idea(title: str, idea_type: str = "product") -> dict:
    return {
        "id":                    uuid.uuid4().hex[:8],
        "title":                 title,
        "idea_type":             idea_type,
        "created_at":            datetime.now().isoformat(),
        "updated_at":            datetime.now().isoformat(),
        "messages":              [],
        "prd":                   empty_prd(),
        "flowchart":             "",
        "competitor_analysis":   {},
        "ai_prompt":             "",
        "test_cases":            {},
        "outline":               {},
        "completeness":          0,
        "milestones_celebrated": [],
    }

# ─── PRD → Markdown（产品模式）────────────────────────────────────────────────
def _render_functional_req(val: list, out: list):
    sub_fields = [("desc","功能说明"),("entry","入口与路径"),("interaction","交互逻辑"),
                  ("fields","字段说明"),("actions","操作行为"),("error_handling","异常处理"),
                  ("permissions","权限控制")]
    for f in val:
        out.append(f"### {f.get('module', '模块')}\n")
        for fk, flabel in sub_fields:
            if f.get(fk):
                out += [f"**{flabel}：** {f[fk]}", ""]
        out.append("")

def prd_to_md(prd: dict, full: bool = False) -> str:
    if not prd:
        return "_PRD 将在对话过程中自动填充..._"
    out = []
    for key, label in PRD_MODULES:
        val         = prd.get(key)
        is_list     = isinstance(val, list)
        has_content = (len(val) > 0) if is_list else bool(val)
        if not has_content and not full:
            continue
        out.append(f"## {label}\n")
        if not has_content:
            hint = EXPORT_HINTS.get(key, "_待填写_")
            if isinstance(hint, list):
                for i, item in enumerate(hint, 1):
                    out.append(f"{i}. {item}")
            else:
                out.append(hint)
            out.append("")
            continue
        if key == "functional_req" and is_list:
            _render_functional_req(val, out)
        elif is_list:
            for i, item in enumerate(val, 1):
                out.append(f"{i}. {item}")
            out.append("")
        else:
            out += [str(val), ""]
    return "\n".join(out) or ("_PRD 生成中..._" if not full else "")

# ─── Outline → Markdown（文学模式）────────────────────────────────────────────
def outline_to_md(outline: dict, section: str = "story") -> str:
    """
    section:
      "story"  — 故事大纲（logline/genre/world/characters/conflict/plot）
      "plan"   — 写作计划（writing_plan）
      "refs"   — 参考资料（references）
      "full"   — 完整创作蓝图（用于导出）
    """
    if not outline:
        return "_大纲将在对话过程中自动填充..._"
    out = []

    def _add(title: str, content):
        if content:
            out.append(f"## {title}\n")
            out.append(str(content))
            out.append("")

    if section in ("story", "full"):
        _add("故事核心（Logline）", outline.get("logline"))
        _add("类型与风格",         outline.get("genre"))
        _add("世界观与背景",       outline.get("world"))
        chars = outline.get("characters", [])
        if chars:
            out.append("## 人物档案\n")
            for c in chars:
                out.append(f"### {c.get('name', '人物')}")
                if c.get("role"):        out.append(f"**角色定位：** {c['role']}")
                if c.get("personality"): out.append(f"**性格特征：** {c['personality']}")
                if c.get("arc"):         out.append(f"**人物弧光：** {c['arc']}")
                out.append("")
        _add("核心冲突", outline.get("conflict"))
        plot = outline.get("plot", {})
        if plot and isinstance(plot, dict) and any(plot.values()):
            out.append("## 故事结构\n")
            for k, lbl in [("opening","开篇事件"),("rising","发展阶段"),
                            ("climax","高潮转折"),("resolution","结局走向")]:
                if plot.get(k):
                    out.append(f"**{lbl}：** {plot[k]}")
            out.append("")

    if section in ("plan", "full"):
        wp = outline.get("writing_plan", {})
        if wp and isinstance(wp, dict) and any(wp.values()):
            out.append("## 写作计划\n")
            for k, lbl in [("perspective","叙事视角"),("entry_character","切入角色"),
                            ("entry_event","切入事件"),("chapter_rhythm","章节节奏")]:
                if wp.get(k):
                    out.append(f"**{lbl}：** {wp[k]}")
            out.append("")

    if section in ("refs", "full"):
        refs = outline.get("references", [])
        if refs:
            out.append("## 参考资料\n")
            for i, r in enumerate(refs, 1):
                out.append(f"{i}. {r}")
            out.append("")

    return "\n".join(out) or "_大纲生成中..._"

def lit_export_md(idea: dict) -> str:
    title   = idea.get("title", "未命名")
    outline = idea.get("outline", {})
    header  = f"# {title} — 创作蓝图\n\n_生成于：{datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n---\n\n"
    return header + outline_to_md(outline, section="full")

# ─── Competitor / Test → Markdown ─────────────────────────────────────────────
def competitor_to_md(ca: dict) -> str:
    if not ca:
        return "_点击「分析竞品」生成竞品调研与可行性报告..._"
    out = []
    if ca.get("summary"):
        out += ["## 市场概况\n", ca["summary"], ""]
    for c in ca.get("competitors", []):
        out.append(f"### {c.get('name', '')}")
        if c.get("description"): out.append(c["description"])
        if c.get("strengths"):   out += ["**优势：**"] + [f"- ✅ {s}" for s in c["strengths"]]
        if c.get("weaknesses"):  out += ["**劣势：**"] + [f"- ❌ {w}" for w in c["weaknesses"]]
        if c.get("url"):         out.append(f"[官网]({c['url']})")
        out.append("")
    if ca.get("market_gap"):      out += ["## 市场机会\n", ca["market_gap"], ""]
    if ca.get("differentiation"): out += ["## 差异化建议\n", ca["differentiation"], ""]
    feas = ca.get("feasibility", {})
    if feas:
        score = feas.get("score", 0)
        out += [f"## 可行性评分：{score}/10  {'⭐' * min(score, 10)}\n"]
        if feas.get("rationale"):       out += [feas["rationale"], ""]
        if feas.get("recommendations"): out += ["**行动建议：**"] + [f"- {r}" for r in feas["recommendations"]]
    return "\n".join(out)

def test_cases_to_md(tc: dict) -> str:
    if not tc:
        return "_点击「生成测试用例」自动生成测试文档..._"
    out = []
    if tc.get("summary"): out += ["## 测试要点\n", tc["summary"], ""]
    for group in tc.get("test_groups", []):
        out.append(f"## {group.get('module', '功能模块')}\n")
        for case in group.get("cases", []):
            pri = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(case.get("priority", ""), "⚪")
            out.append(f"### {pri} {case.get('id', '')}：{case.get('scenario', '')}")
            if case.get("preconditions"): out.append(f"**前置条件：** {case['preconditions']}")
            if case.get("steps"):
                out.append("**操作步骤：**")
                for s in case["steps"]: out.append(f"- {s}")
            if case.get("expected"): out.append(f"**预期结果：** {case['expected']}")
            out.append("")
    return "\n".join(out)

# ─── Secondary AI calls ───────────────────────────────────────────────────────
def gen_flowchart(idea: dict) -> str:
    try:
        raw = call_api([
            {"role": "system", "content": "根据以下PRD生成Mermaid flowchart代码，只输出代码（以flowchart TD开头），节点标签用双引号。"},
            {"role": "user",   "content": prd_to_md(idea.get("prd", {}))},
        ])
        m = re.search(r"(flowchart\s+(?:TD|LR|BT|RL)[\s\S]+)", raw)
        return m.group(1).strip() if m else raw.strip()
    except Exception:
        return ""

def gen_competitor(idea: dict) -> tuple[dict, str]:
    prd_text = prd_to_md(idea.get("prd", {}))
    try:
        if st.session_state.get("cfg_websearch"):
            raw = call_responses_api(
                instructions=COMPETITOR_PROMPT,
                user_input=f"请联网搜索并分析以下产品的竞品：\n\n{prd_text}",
            )
        else:
            raw = call_api([
                {"role": "system", "content": COMPETITOR_PROMPT},
                {"role": "user",   "content": f"请分析以下产品的竞品情况：\n\n{prd_text}"},
            ])
        result = extract_json(raw)
        return (result, "") if result else ({}, f"解析失败：{raw[:300]}")
    except Exception as e:
        return {}, str(e)

def gen_wireframe(idea: dict) -> str:
    try:
        return call_api([
            {"role": "system", "content": WIREFRAME_PROMPT},
            {"role": "user",   "content": f"请根据以下PRD生成各核心页面的ASCII线框图：\n\n{prd_to_md(idea.get('prd', {}), full=True)}"},
        ])
    except Exception:
        return ""

def gen_test_cases(idea: dict) -> tuple[dict, str]:
    try:
        raw = call_api([
            {"role": "system", "content": TEST_CASE_PROMPT},
            {"role": "user",   "content": f"基于以下PRD生成测试用例：\n\n{prd_to_md(idea.get('prd', {}))}"},
        ])
        result = extract_json(raw)
        return (result, "") if result else ({}, f"解析失败：{raw[:300]}")
    except Exception as e:
        return {}, str(e)

# ─── Edit diff & AI sync helpers ─────────────────────────────────────────────
def _compute_prd_diff(old: dict, new: dict) -> list[str]:
    """返回有内容变更的 PRD 字段中文名列表。"""
    changed = []
    for key, label in PRD_MODULES:
        if json.dumps(old.get(key), ensure_ascii=False, sort_keys=True) != \
           json.dumps(new.get(key), ensure_ascii=False, sort_keys=True):
            changed.append(label)
    return changed

_OUTLINE_LABELS = {
    "logline": "故事核心", "genre": "类型与风格", "world": "世界观与背景",
    "characters": "人物档案", "conflict": "核心冲突", "plot": "故事结构",
    "writing_plan": "写作计划", "references": "参考资料",
}

def _compute_outline_diff(old: dict, new: dict) -> list[str]:
    """返回有内容变更的 outline 字段中文名列表。"""
    return [
        lbl for key, lbl in _OUTLINE_LABELS.items()
        if json.dumps(old.get(key), ensure_ascii=False, sort_keys=True) !=
           json.dumps(new.get(key), ensure_ascii=False, sort_keys=True)
    ]

def _append_edit_notification(idea: dict, changed_fields: list[str]):
    """向对话历史追加一条对用户不可见的系统通知，告知 AI 哪些字段被手动修改。"""
    if not changed_fields:
        return
    fields_str = "、".join(changed_fields)
    idea["messages"].append({
        "role":    "user",
        "content": (
            f"[系统通知] 用户刚刚手动更新了以下内容：{fields_str}。"
            "请基于最新内容继续提问，不要重复询问用户已经填写的部分。"
            "用户手动编辑的内容具有最高优先级，不要在后续回复中覆盖这些字段。"
        ),
        "hidden": True,
    })

# ─── Session state defaults ───────────────────────────────────────────────────
_DEFAULTS = {
    "page":                 "home",
    "idea":                 None,
    "processing":           False,
    "edit_mode":            False,
    "comp_loading":         False,
    "comp_error":           "",
    "prompt_loading":       False,
    "flow_loading":         False,
    "test_loading":         False,
    "test_error":           "",
    "suggest_flow_refresh": False,
    "new_milestone":        0,
    "stage3_choice":        "",
    "new_idea_type":        "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ═══════════════════════════════════════════════════════════════════════════════
def page_home():
    st.title("💡 Idea 需求分析器")
    st.caption("将模糊灵感转化为专业可落地的需求文档 · 竞品分析 · AI开发Prompt · 测试用例 · 文学创作蓝图")
    st.markdown("---")

    if not is_configured():
        st.warning("⚠️ 请先在左侧侧边栏填写 API 地址和 Key，然后开始使用。")
        return

    if st.button("➕ 新建创意", type="primary"):
        st.session_state.page         = "new"
        st.session_state.new_idea_type = ""
        st.rerun()

    ideas = list_ideas()
    if not ideas:
        st.info("还没有创意，点击「新建创意」开始第一个！")
        return

    st.subheader(f"我的创意（{len(ideas)} 个）")
    for idea in ideas:
        c1, c2, c3, c4, c5 = st.columns([5, 2, 2, 1, 1])
        with c1:
            badge = "📦" if idea.get("idea_type", "product") == "product" else "✍️"
            st.markdown(f"{badge} **{idea['title']}**")
        with c2:
            ts = idea["updated_at"][:16].replace("T", " ") if idea["updated_at"] else "-"
            st.caption(ts)
        with c3:
            pct = idea["completeness"]
            st.progress(pct / 100, text=f"{pct}%")
        with c4:
            if st.button("打开", key=f"open_{idea['id']}"):
                d = load_idea(idea["id"])
                if d:
                    st.session_state.idea      = d
                    st.session_state.edit_mode = False
                    st.session_state.page      = "workspace"
                    st.rerun()
        with c5:
            if st.button("删除", key=f"del_{idea['id']}"):
                delete_idea(idea["id"])
                st.rerun()
        st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: NEW IDEA
# ═══════════════════════════════════════════════════════════════════════════════
def page_new():
    if st.button("← 返回"):
        st.session_state.page          = "home"
        st.session_state.new_idea_type = ""
        st.rerun()
    st.title("新建创意")

    # Step 1: 选择类型
    if not st.session_state.get("new_idea_type"):
        st.subheader("选择创意类型")
        st.markdown("你的这个 idea，是要做个产品，还是写一个故事？")
        col_a, col_b = st.columns(2)
        with col_a:
            with st.container(border=True):
                st.markdown("### 📦 产品需求")
                st.caption("帮你把产品 idea 梳理成专业需求文档")
                st.markdown("- 🔍 竞品分析\n- 📋 13模块PRD\n- 🤖 AI开发Prompt\n- 🧪 测试用例")
                if st.button("选择 产品需求 →", type="primary", use_container_width=True):
                    st.session_state.new_idea_type = "product"
                    st.rerun()
        with col_b:
            with st.container(border=True):
                st.markdown("### ✍️ 文学创作")
                st.caption("帮你把故事 idea 梳理成完整创作蓝图")
                st.markdown("- 📖 故事大纲\n- 👤 人物档案\n- 🗺️ 写作计划\n- 📚 参考资料")
                if st.button("选择 文学创作 →", use_container_width=True):
                    st.session_state.new_idea_type = "literature"
                    st.rerun()
        return

    # Step 2: 填写描述
    itype      = st.session_state.new_idea_type
    type_label = "📦 产品需求" if itype == "product" else "✍️ 文学创作"
    st.caption(f"已选择：{type_label}")

    placeholder = (
        "例如：我想做一款帮助大学生找兼职的App…"
        if itype == "product"
        else "例如：我想写一个关于末日后人类重建文明的故事…"
    )
    label = "✏️ 用自己的话描述你的想法：" if itype == "product" else "✏️ 简单描述你的故事 idea："

    with st.form("new_form", clear_on_submit=True):
        idea_text = st.text_area(label, placeholder=placeholder, height=160,
                                 help="不需要很完整，一两句话就行，AI会引导你深入挖掘")
        go = st.form_submit_button("🚀 开始梳理", type="primary", use_container_width=True)

    if go and idea_text.strip():
        raw_title = idea_text.strip()
        title     = (raw_title[:18] + "…") if len(raw_title) > 18 else raw_title
        d         = new_idea(title, idea_type=itype)
        prefix    = "我的产品想法是：" if itype == "product" else "我的故事想法是："
        d["messages"].append({"role": "user", "content": f"{prefix}{raw_title}"})
        save_idea(d)
        st.session_state.idea          = d
        st.session_state.edit_mode     = False
        st.session_state.processing    = True
        st.session_state.new_milestone = 0
        st.session_state.stage3_choice = ""
        st.session_state.new_idea_type = ""
        st.session_state.page          = "workspace"
        st.rerun()

# ─── PRD editor component ─────────────────────────────────────────────────────
def render_prd_editor(idea: dict):
    prd = idea.get("prd", empty_prd())
    iid = idea["id"]
    st.caption("修改后点击「退出编辑」自动保存。列表字段每行一条。")
    for key, label in PRD_MODULES:
        st.markdown(f"**{label}**")
        val        = prd.get(key, [] if key in LIST_FIELDS | FEATURE_FIELDS else "")
        widget_key = f"prd_{iid}_{key}"
        if key == "functional_req":
            val_str = json.dumps(val, ensure_ascii=False, indent=2) if isinstance(val, list) else "[]"
            new_val = st.text_area(label, value=val_str, height=200, key=widget_key,
                                   label_visibility="collapsed",
                                   help='JSON格式：[{"module":"模块名","desc":"...","entry":"..."}]')
            try: prd[key] = json.loads(new_val)
            except json.JSONDecodeError: pass
        elif key in LIST_FIELDS:
            val_str = "\n".join(val) if isinstance(val, list) else str(val)
            new_val = st.text_area(label, value=val_str, height=100, key=widget_key,
                                   label_visibility="collapsed", help="每行一条")
            prd[key] = [ln for ln in new_val.splitlines() if ln.strip()]
        else:
            new_val  = st.text_area(label, value=val or "", height=80, key=widget_key,
                                    label_visibility="collapsed")
            prd[key] = new_val
    idea["prd"] = prd

# ─── Outline editor component（文学模式）────────────────────────────────────
def render_outline_editor(idea: dict):
    outline = idea.get("outline", {}) or {}
    iid     = idea["id"]
    st.caption("修改后点击「完成编辑」自动保存并通知 AI。")

    for key, label, height in [
        ("logline",  "故事核心（Logline）", 60),
        ("genre",    "类型与风格",          60),
        ("world",    "世界观与背景",        100),
        ("conflict", "核心冲突",            80),
    ]:
        st.markdown(f"**{label}**")
        new_val = st.text_area(label, value=outline.get(key) or "", height=height,
                               key=f"ol_{iid}_{key}", label_visibility="collapsed")
        outline[key] = new_val

    st.markdown("**人物档案（JSON 格式）**")
    chars_val = json.dumps(outline.get("characters", []), ensure_ascii=False, indent=2)
    new_chars = st.text_area("characters", value=chars_val, height=200,
                             key=f"ol_{iid}_characters", label_visibility="collapsed",
                             help='[{"name":"名","role":"角色","personality":"性格","arc":"弧光"}]')
    try:
        outline["characters"] = json.loads(new_chars)
    except json.JSONDecodeError:
        pass

    st.markdown("**故事结构**")
    plot = dict(outline.get("plot") or {})
    for k, lbl, h in [("opening","开篇事件",60),("rising","发展阶段",80),
                       ("climax","高潮转折",60),("resolution","结局走向",60)]:
        st.caption(lbl)
        new_val = st.text_area(lbl, value=plot.get(k) or "", height=h,
                               key=f"ol_{iid}_plot_{k}", label_visibility="collapsed")
        plot[k] = new_val
    outline["plot"] = plot

    st.markdown("**写作计划**")
    wp = dict(outline.get("writing_plan") or {})
    for k, lbl, h in [("perspective","叙事视角",60),("entry_character","切入角色",60),
                       ("entry_event","切入事件",60),("chapter_rhythm","章节节奏",100)]:
        st.caption(lbl)
        new_val = st.text_area(lbl, value=wp.get(k) or "", height=h,
                               key=f"ol_{iid}_wp_{k}", label_visibility="collapsed")
        wp[k] = new_val
    outline["writing_plan"] = wp

    st.markdown("**参考资料**（每行一条）")
    refs     = outline.get("references", [])
    refs_str = "\n".join(refs) if isinstance(refs, list) else str(refs or "")
    new_refs = st.text_area("references", value=refs_str, height=100,
                            key=f"ol_{iid}_references", label_visibility="collapsed")
    outline["references"] = [ln for ln in new_refs.splitlines() if ln.strip()]

    idea["outline"] = outline

# ─── Progress panel（产品模式）────────────────────────────────────────────────
def render_progress_panel(idea: dict):
    prd       = idea.get("prd", {})
    pct       = idea.get("completeness", 0)
    completed = get_completed_stages(idea)
    current   = get_current_guided_stage(idea)

    st.metric("需求完整度", f"{pct}%")
    st.progress(pct / 100)
    st.markdown("---")

    st.markdown("**梳理进度**")
    for s in GUIDED_STAGES:
        done   = s["id"] in completed
        active = s["id"] == current
        icon   = "✅" if done else ("▶️" if active else "⭕")
        weight = "**" if active else ""
        st.markdown(f"{icon} {weight}{s['emoji']} {s['title']}{weight}")
        if active: st.caption(f"　　{s['desc']}")
    icon4 = "✅" if current == 4 else "⭕"
    st.markdown(f"{icon4} 🔬 深化完善")

    st.markdown("---")
    st.markdown("**已生成产出**")
    has_prd = any(field_filled(prd, k) for k, _ in PRD_MODULES)
    for done, label in [
        (has_prd,                               "📋 需求文档"),
        (bool(idea.get("flowchart")),           "🗺️ 流程图"),
        (bool(idea.get("competitor_analysis")), "🔍 竞品分析"),
        (bool(idea.get("ai_prompt")),           "🎨 ASCII原型图"),
        (bool(idea.get("test_cases")),          "🧪 测试用例"),
    ]:
        st.markdown(f"{'✅' if done else '⭕'} {label}")

    st.markdown("---")
    msg_count = len([m for m in idea.get("messages", []) if m["role"] == "user"])
    st.caption(f"已回答 {msg_count} 个问题")

# ─── Progress panel（文学模式）────────────────────────────────────────────────
def render_progress_panel_lit(idea: dict):
    outline   = idea.get("outline", {})
    pct       = idea.get("completeness", 0)
    completed = get_lit_completed_stages(idea)
    current   = get_lit_current_stage(idea)

    st.metric("创作完整度", f"{pct}%")
    st.progress(pct / 100)
    st.markdown("---")

    st.markdown("**梳理进度**")
    for s in LIT_STAGES:
        done   = s["id"] in completed
        active = s["id"] == current
        icon   = "✅" if done else ("▶️" if active else "⭕")
        weight = "**" if active else ""
        st.markdown(f"{icon} {weight}{s['emoji']} {s['title']}{weight}")
        if active: st.caption(f"　　{s['desc']}")

    st.markdown("---")
    st.markdown("**已生成产出**")
    for done, label in [
        (bool(outline),                              "📖 故事大纲"),
        (lit_field_filled(outline, "writing_plan"),  "🗺️ 写作计划"),
        (lit_field_filled(outline, "references"),    "📚 参考资料"),
    ]:
        st.markdown(f"{'✅' if done else '⭕'} {label}")

    st.markdown("---")
    msg_count = len([m for m in idea.get("messages", []) if m["role"] == "user"])
    st.caption(f"已回答 {msg_count} 个问题")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: WORKSPACE
# ═══════════════════════════════════════════════════════════════════════════════
def page_workspace():
    idea = st.session_state.idea
    if not idea:
        st.session_state.page = "home"
        st.rerun()
        return

    itype = idea.get("idea_type", "product")

    tb1, tb2, tb3 = st.columns([1, 8, 1])
    with tb1:
        if st.button("← 返回"):
            save_idea(idea)
            st.session_state.idea = None
            st.session_state.page = "home"
            st.rerun()
    with tb2:
        badge = "📦" if itype == "product" else "✍️"
        st.markdown(f"{badge} **{idea['title']}**")
    with tb3:
        if st.button("💾 保存"):
            save_idea(idea)
            st.toast("已保存 ✓")

    if itype == "product":
        _workspace_product(idea)
    else:
        _workspace_literature(idea)

# ─── Product mode workspace ───────────────────────────────────────────────────
def _workspace_product(idea: dict):
    if idea.get("completeness", 0) >= 85:
        st.success("🎉 需求梳理完成！右侧各 Tab 可查看/导出所有产出。")

    left, mid, right = st.columns([4, 2, 5], gap="medium")

    with mid:
        render_progress_panel(idea)

    with right:
        tab_prd, tab_flow, tab_comp, tab_wire, tab_test = st.tabs(
            ["📋 需求文档", "🗺️ 流程图", "🔍 竞品分析", "🎨 ASCII原型图", "🧪 测试用例"]
        )

        with tab_prd:
            b1, b2 = st.columns(2)
            with b1:
                edit_lbl = "✅ 完成编辑" if st.session_state.edit_mode else "✏️ 手动编辑PRD"
                if st.button(edit_lbl, use_container_width=True):
                    if st.session_state.edit_mode:
                        # 退出编辑：diff → 通知 AI → 保存
                        old_prd  = idea.pop("_edit_snapshot", {})
                        changed  = _compute_prd_diff(old_prd, idea.get("prd", {}))
                        if changed:
                            _append_edit_notification(idea, changed)
                            st.session_state.processing = True
                        save_idea(idea)
                        st.toast("保存成功 ✓")
                        st.session_state.suggest_flow_refresh = True
                    else:
                        # 进入编辑：保存当前 PRD 快照
                        idea["_edit_snapshot"] = json.loads(
                            json.dumps(idea.get("prd", {}), ensure_ascii=False)
                        )
                    st.session_state.edit_mode = not st.session_state.edit_mode
                    st.rerun()
            with b2:
                st.download_button("📄 导出完整PRD", data=prd_to_md(idea.get("prd", {}), full=True),
                                   file_name=f"{idea['title']}_PRD.md", mime="text/markdown",
                                   use_container_width=True)
            if st.session_state.get("suggest_flow_refresh"):
                st.info("PRD已更新，建议同步刷新流程图。")
                if st.button("🔄 立即刷新流程图"):
                    st.session_state.flow_loading = True
                    st.session_state.suggest_flow_refresh = False
                    st.rerun()
            if st.session_state.edit_mode:
                render_prd_editor(idea)
            else:
                md = prd_to_md(idea.get("prd", {}), full=False)
                if md.startswith("_PRD"):
                    st.info("对话开始后，PRD将在这里实时更新。")
                else:
                    st.markdown(md)

        with tab_flow:
            if st.button("🔄 根据最新PRD刷新流程图", use_container_width=True):
                st.session_state.flow_loading = True
                st.session_state.suggest_flow_refresh = False
                st.rerun()
            if st.session_state.flow_loading:
                with st.spinner("正在生成流程图..."):
                    fc = gen_flowchart(idea)
                    if fc:
                        idea["flowchart"] = fc
                        save_idea(idea)
                st.session_state.flow_loading = False
                st.rerun()
            if idea.get("flowchart"):
                render_mermaid(idea["flowchart"])
            else:
                st.info("流程图将在对话开始后自动生成，也可点击上方按钮手动刷新。")

        with tab_comp:
            ws = st.session_state.get("cfg_websearch", False)
            st.caption("🌐 联网实时搜索" if ws else "📚 基于AI训练知识（可在侧边栏开启联网搜索）")
            if st.button("🔍 分析竞品与落地可行性", type="primary", use_container_width=True):
                st.session_state.comp_loading = True
                st.session_state.comp_error   = ""
                st.rerun()
            if st.session_state.get("comp_loading"):
                label = "AI正在联网搜索竞品（约30-60秒）..." if ws else "AI正在分析竞品..."
                with st.spinner(label):
                    ca, err = gen_competitor(idea)
                    if ca:
                        idea["competitor_analysis"] = ca
                        save_idea(idea)
                    st.session_state.comp_error = err
                st.session_state.comp_loading = False
                st.rerun()
            if st.session_state.get("comp_error"):
                st.error(f"分析失败：{st.session_state.comp_error}")
            st.markdown(competitor_to_md(idea.get("competitor_analysis", {})))

        with tab_wire:
            if st.button("🎨 生成ASCII原型图", type="primary", use_container_width=True):
                st.session_state.prompt_loading = True
                st.rerun()
            if st.session_state.prompt_loading:
                with st.spinner("AI正在绘制ASCII原型图（可能需要30-60秒）..."):
                    wf = gen_wireframe(idea)
                    if wf:
                        idea["ai_prompt"] = wf
                        save_idea(idea)
                st.session_state.prompt_loading = False
                st.rerun()
            if idea.get("ai_prompt"):
                st.download_button("📥 下载原型图文件", data=idea["ai_prompt"],
                                   file_name=f"{idea['title']}_原型图.txt",
                                   mime="text/plain", use_container_width=True)
                st.code(idea["ai_prompt"], language="text")
            else:
                st.info("需求梳理完成后，点击上方按钮生成各核心页面的ASCII线框图，可直接喂给 AI 辅助还原视觉稿。")

        with tab_test:
            if st.button("🧪 生成测试用例", type="primary", use_container_width=True):
                st.session_state.test_loading = True
                st.session_state.test_error   = ""
                st.rerun()
            if st.session_state.get("test_loading"):
                with st.spinner("正在生成测试用例..."):
                    tc, err = gen_test_cases(idea)
                    if tc:
                        idea["test_cases"] = tc
                        save_idea(idea)
                    st.session_state.test_error = err
                st.session_state.test_loading = False
                st.rerun()
            if st.session_state.get("test_error"):
                st.error(f"生成失败：{st.session_state.test_error}")
            if idea.get("test_cases"):
                st.download_button("📋 导出测试文档",
                                   data=test_cases_to_md(idea.get("test_cases", {})),
                                   file_name=f"{idea['title']}_TestCases.md",
                                   mime="text/markdown", use_container_width=True)
                st.markdown(test_cases_to_md(idea.get("test_cases", {})))
            else:
                st.info("需求梳理完成后，点击上方按钮生成测试用例。")

    with left:
        _chat_product(idea)

# ─── Literature mode workspace ────────────────────────────────────────────────
def _workspace_literature(idea: dict):
    if idea.get("completeness", 0) >= 85:
        st.success("🎉 创作蓝图梳理完成！右侧各 Tab 可查看/导出所有产出。")

    left, mid, right = st.columns([4, 2, 5], gap="medium")

    with mid:
        render_progress_panel_lit(idea)

    with right:
        tab_story, tab_plan, tab_refs, tab_export = st.tabs(
            ["📖 故事大纲", "🗺️ 写作计划", "📚 参考资料", "📤 导出"]
        )

        with tab_story:
            b1, b2 = st.columns(2)
            with b1:
                edit_lbl = "✅ 完成编辑" if st.session_state.edit_mode else "✏️ 手动编辑大纲"
                if st.button(edit_lbl, use_container_width=True, key="lit_edit_btn"):
                    if st.session_state.edit_mode:
                        old_outline = idea.pop("_edit_snapshot", {})
                        changed     = _compute_outline_diff(old_outline, idea.get("outline", {}))
                        if changed:
                            _append_edit_notification(idea, changed)
                            st.session_state.processing = True
                        save_idea(idea)
                        st.toast("保存成功 ✓")
                    else:
                        idea["_edit_snapshot"] = json.loads(
                            json.dumps(idea.get("outline", {}), ensure_ascii=False)
                        )
                    st.session_state.edit_mode = not st.session_state.edit_mode
                    st.rerun()
            with b2:
                st.download_button("📥 导出创作蓝图", data=lit_export_md(idea),
                                   file_name=f"{idea['title']}_创作蓝图.md",
                                   mime="text/markdown", use_container_width=True,
                                   key="lit_dl_story")
            if st.session_state.edit_mode:
                render_outline_editor(idea)
            else:
                md = outline_to_md(idea.get("outline", {}), section="story")
                if md.startswith("_大纲"):
                    st.info("对话开始后，故事大纲将在这里实时更新。")
                else:
                    st.markdown(md)

        with tab_plan:
            md = outline_to_md(idea.get("outline", {}), section="plan")
            if md.startswith("_大纲"):
                st.info("写作计划将在对话后期生成。")
            else:
                st.markdown(md)

        with tab_refs:
            md = outline_to_md(idea.get("outline", {}), section="refs")
            if md.startswith("_大纲"):
                st.info("参考资料将在对话后期自动推荐。")
            else:
                st.markdown(md)

        with tab_export:
            st.download_button(
                "📥 导出完整创作蓝图",
                data=lit_export_md(idea),
                file_name=f"{idea['title']}_创作蓝图.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True,
            )
            st.markdown("---")
            preview = outline_to_md(idea.get("outline", {}), section="full")
            if preview.startswith("_大纲"):
                st.info("对话完成后，完整创作蓝图将在这里预览。")
            else:
                st.markdown(preview)

    with left:
        _chat_literature(idea)

# ─── 里程碑庆祝横幅（共用）────────────────────────────────────────────────────
def _render_milestone_banner(idea: dict, stages: list, is_lit: bool = False):
    milestone = st.session_state.get("new_milestone", 0)
    if not milestone:
        return
    total  = len(stages)
    s_info = stages[milestone - 1]

    if milestone < total:
        st.balloons()
        with st.container(border=True):
            st.success(
                f"🎉 **阶段 {milestone} 完成：{s_info['title']}！**\n\n"
                f"你已经把{s_info['desc'].replace('·', '、')}都想清楚了，继续加油！"
            )
            if st.button("继续梳理下一阶段 →", type="primary", use_container_width=True,
                         key="milestone_continue"):
                st.session_state.new_milestone = 0
                st.rerun()
    else:
        st.balloons()
        with st.container(border=True):
            if is_lit:
                st.success("🎊 **创作蓝图梳理完成！所有阶段全部达成！**")
                st.markdown(
                    "故事的世界观、人物、冲突、结构和写作计划都已理清楚了！\n\n"
                    "**点击右侧「📤 导出」Tab 下载完整创作蓝图，带着它开始动笔吧！**"
                )
                st.markdown("---")
                ca, cb = st.columns(2)
                with ca:
                    if st.button("📤 去导出创作蓝图", type="primary", use_container_width=True,
                                 key="lit_goto_export"):
                        st.session_state.new_milestone = 0
                        st.rerun()
                with cb:
                    if st.button("💪 继续完善更多细节", use_container_width=True,
                                 key="lit_continue"):
                        st.session_state.new_milestone = 0
                        st.rerun()
            else:
                st.success("🎊 **基础需求梳理完成！三个阶段全部达成！**")
                st.markdown(
                    "你已经把产品 **是什么、给谁用、怎么做** 都想清楚了！\n\n"
                    "**现在可以生成 ASCII 原型图** —— 把视觉布局描述清楚，直接喂给 AI 快速还原界面！"
                )
                st.markdown("---")
                ca, cb = st.columns(2)
                with ca:
                    if st.button("🎨 先生成ASCII原型图", type="primary", use_container_width=True,
                                 key="prod_gen_prompt"):
                        st.session_state.new_milestone  = 0
                        st.session_state.stage3_choice  = "prompt"
                        st.session_state.prompt_loading = True
                        st.rerun()
                with cb:
                    if st.button("💪 继续深化，完善更多细节", use_container_width=True,
                                 key="prod_continue"):
                        st.session_state.new_milestone = 0
                        st.session_state.stage3_choice = "continue"
                        st.rerun()

# ─── Product mode chat ────────────────────────────────────────────────────────
def _chat_product(idea: dict):
    st.subheader("对话")
    done_count = len(get_completed_stages(idea))
    st.progress(done_count / 3, text=f"引导进度：{done_count} / 3 个阶段完成")

    _render_milestone_banner(idea, GUIDED_STAGES, is_lit=False)

    if st.session_state.get("stage3_choice") == "prompt" and idea.get("ai_prompt"):
        st.info("✅ ASCII原型图已生成！点击右侧「🎨 ASCII原型图」Tab 查看和下载。")

    st.markdown("---")
    _render_chat_history(idea)

    hide_input = (
        st.session_state.get("new_milestone") == len(GUIDED_STAGES)
        or (st.session_state.get("stage3_choice") == "prompt" and not idea.get("ai_prompt"))
    )
    if not st.session_state.processing and not hide_input:
        answer = st.chat_input("回答问题…（不知道说「跳过」，AI会自动填默认值）")
        if answer:
            idea["messages"].append({"role": "user", "content": answer})
            st.session_state.processing = True
            save_idea(idea)
            st.rerun()

    if st.session_state.processing:
        _process_product_response(idea)

# ─── Literature mode chat ─────────────────────────────────────────────────────
def _chat_literature(idea: dict):
    st.subheader("对话")
    done_count = len(get_lit_completed_stages(idea))
    total      = len(LIT_STAGES)
    st.progress(done_count / total, text=f"引导进度：{done_count} / {total} 个阶段完成")

    _render_milestone_banner(idea, LIT_STAGES, is_lit=True)

    st.markdown("---")
    _render_chat_history(idea)

    hide_input = st.session_state.get("new_milestone") == len(LIT_STAGES)
    if not st.session_state.processing and not hide_input:
        answer = st.chat_input("回答问题…（不知道说「跳过」，AI会自动填默认值）")
        if answer:
            idea["messages"].append({"role": "user", "content": answer})
            st.session_state.processing = True
            save_idea(idea)
            st.rerun()

    if st.session_state.processing:
        _process_literature_response(idea)

# ─── 对话历史渲染（共用）──────────────────────────────────────────────────────
def _render_chat_history(idea: dict):
    for msg in idea.get("messages", []):
        if msg.get("hidden"):   # 系统通知，对用户不可见
            continue
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"])
            else:
                d = msg.get("display", {})
                if d.get("analysis"):  st.caption(f"💭 {d['analysis']}")
                if d.get("question"):
                    badge = f"`{d.get('category','')}`" if d.get("category") else ""
                    st.markdown(f"**问** {badge}：{d['question']}")
                elif d.get("done"):
                    st.success("✅ 梳理完成！查看右侧各Tab获取产出。")
                else:
                    st.write(msg.get("content", ""))

# ─── 里程碑检测（共用）────────────────────────────────────────────────────────
def _check_and_celebrate(idea: dict, stages_before: set, stages_after: list):
    newly_completed  = set(stages_after) - stages_before
    celebrated_list  = idea.get("milestones_celebrated", [])
    new_uncelebrated = [s for s in sorted(newly_completed) if s not in celebrated_list]
    if new_uncelebrated:
        newest = new_uncelebrated[-1]
        celebrated_list.append(newest)
        idea["milestones_celebrated"] = celebrated_list
        st.session_state.new_milestone = newest

# ─── Product mode AI response ─────────────────────────────────────────────────
def _process_product_response(idea: dict):
    msgs = idea.get("messages", [])
    if not (msgs and msgs[-1]["role"] == "user"):
        return
    stages_before = set(get_completed_stages(idea))
    history       = msgs[-HISTORY_LIMIT:]
    api_msgs = (
        [{"role": "system", "content": MAIN_PROMPT},
         {"role": "system", "content": get_stage_prompt(idea)}]
        + [{"role": m["role"], "content": m["content"]} for m in history]
    )
    with st.chat_message("assistant"):
        thinking  = st.empty()
        full_text = ""
        thinking.markdown("💭 _AI正在思考..._")
        try:
            for chunk in call_api_streaming(api_msgs):
                full_text += chunk
        except Exception:
            try:
                full_text = call_api(api_msgs)
            except Exception as e:
                thinking.empty()
                st.error(f"调用失败（已重试 {MAX_RETRY} 次）：{e}")
                st.session_state.processing = False
                st.stop()
        thinking.empty()
        parsed  = extract_json(full_text)
        display = {}
        if parsed:
            if parsed.get("prd"):        idea["prd"]          = parsed["prd"]
            if parsed.get("flowchart"):  idea["flowchart"]    = parsed["flowchart"]
            if "completeness" in parsed: idea["completeness"] = int(parsed.get("completeness", 0))
            analysis = parsed.get("analysis", "")
            question = parsed.get("question")
            category = parsed.get("question_category", "")
            if analysis: st.caption(f"💭 {analysis}")
            if question:
                badge = f"`{category}`" if category else ""
                st.markdown(f"**问** {badge}：{question}")
            else:
                st.success("✅ 梳理完成！查看右侧各Tab获取产出。")
            display = {"analysis": analysis, "question": question,
                       "category": category, "done": question is None}
        else:
            st.warning("响应解析失败，原始内容：")
            st.code(full_text[:800])

    idea["messages"].append({"role": "assistant", "content": full_text, "display": display})
    _check_and_celebrate(idea, stages_before, get_completed_stages(idea))
    save_idea(idea)
    st.session_state.processing = False
    st.rerun()

# ─── Literature mode AI response ──────────────────────────────────────────────
def _process_literature_response(idea: dict):
    msgs = idea.get("messages", [])
    if not (msgs and msgs[-1]["role"] == "user"):
        return
    stages_before = set(get_lit_completed_stages(idea))
    history       = msgs[-HISTORY_LIMIT:]
    api_msgs = (
        [{"role": "system", "content": LIT_PROMPT},
         {"role": "system", "content": get_lit_stage_prompt(idea)}]
        + [{"role": m["role"], "content": m["content"]} for m in history]
    )
    with st.chat_message("assistant"):
        thinking  = st.empty()
        full_text = ""
        thinking.markdown("💭 _AI正在思考..._")
        try:
            for chunk in call_api_streaming(api_msgs):
                full_text += chunk
        except Exception:
            try:
                full_text = call_api(api_msgs)
            except Exception as e:
                thinking.empty()
                st.error(f"调用失败（已重试 {MAX_RETRY} 次）：{e}")
                st.session_state.processing = False
                st.stop()
        thinking.empty()
        parsed  = extract_json(full_text)
        display = {}
        if parsed:
            if parsed.get("outline"):    idea["outline"]      = parsed["outline"]
            if "completeness" in parsed: idea["completeness"] = int(parsed.get("completeness", 0))
            analysis = parsed.get("analysis", "")
            question = parsed.get("question")
            category = parsed.get("question_category", "")
            if analysis: st.caption(f"💭 {analysis}")
            if question:
                badge = f"`{category}`" if category else ""
                st.markdown(f"**问** {badge}：{question}")
            else:
                st.success("✅ 创作蓝图梳理完成！查看右侧各Tab获取产出。")
            display = {"analysis": analysis, "question": question,
                       "category": category, "done": question is None}
        else:
            st.warning("响应解析失败，原始内容：")
            st.code(full_text[:800])

    idea["messages"].append({"role": "assistant", "content": full_text, "display": display})
    _check_and_celebrate(idea, stages_before, get_lit_completed_stages(idea))
    save_idea(idea)
    st.session_state.processing = False
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
{
    "home":      page_home,
    "new":       page_new,
    "workspace": page_workspace,
}.get(st.session_state.page, page_home)()
