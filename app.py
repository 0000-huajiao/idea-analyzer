"""
Idea 需求分析器（开源版）
流式输出 · 三栏布局 · 双模式（产品需求 / 文学创作）· 13模块PRD · 竞品分析 · AI开发Prompt · 测试用例
数据存储在浏览器 Session，不写服务器文件。
"""

import json
import pathlib
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

# ─── Global CSS ───────────────────────────────────────────────────────────────
# Design system: "Midnight Iris"
# Palette inspired by Linear dark + vibrant multi-tone accents
#   bg #0e0e13 | surface #16161e | violet #8b5cf6 | cyan #22d3ee | pink #e879f9
st.markdown("""
<style>
/* ══════════════════════════════════════════════════════════════════
   MIDNIGHT IRIS — Dark Design System
   bg: #0e0e13 | surface: #16161e | accent: #8b5cf6 | cyan: #22d3ee
   ══════════════════════════════════════════════════════════════════ */

/* ── Base app ─────────────────────────────────────────────────────── */
.stApp {
    background: #0e0e13 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
                 'Microsoft YaHei', sans-serif;
}

/* Main body text */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] td,
[data-testid="stMarkdownContainer"] th {
    color: #c4c0d9 !important;
}
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] b {
    color: #eeeaf8 !important;
}
[data-testid="stMarkdownContainer"] code {
    background: #1e1e2e !important;
    color: #a78bfa !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0a0a10 !important;
    border-right: 1px solid #1e1e2c !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: #857fa8 !important;
}
section[data-testid="stSidebar"] h1 {
    color: #eeeaf8 !important;
    font-size: 1.2rem !important;
    letter-spacing: -0.3px !important;
}
section[data-testid="stSidebar"] input {
    background: #16161e !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 8px !important;
    color: #eeeaf8 !important;
}
section[data-testid="stSidebar"] input:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 2px rgba(139,92,246,0.22) !important;
}
/* Sidebar success alert (API key configured) */
section[data-testid="stSidebar"] [data-testid="stAlert"],
section[data-testid="stSidebar"] [data-baseweb="notification"] {
    background: rgba(16,185,129,0.10) !important;
    border: 1px solid rgba(52,211,153,0.22) !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] [data-testid="stAlert"] p,
section[data-testid="stSidebar"] [data-baseweb="notification"] p,
section[data-testid="stSidebar"] [data-baseweb="notification"] span {
    color: #34d399 !important;
}

/* ── Alert / Notification — dark bg fix ───────────────────────────
   Key fix: all baseweb notifications get a dark background so text
   is always readable regardless of its color (fixes yellow-on-yellow) */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    overflow: hidden !important;
}
/* Base: dark slate bg + left accent border for all types */
[data-baseweb="notification"] {
    background: #13121e !important;
    border-radius: 10px !important;
    border: 1px solid #252535 !important;
    border-left: 3px solid #8b5cf6 !important;
}
/* ⚠️ Warning — amber */
[data-baseweb="notification"][kind="warning"] {
    background: #1a1400 !important;
    border-color: #2a2000 !important;
    border-left-color: #f59e0b !important;
}
[data-baseweb="notification"][kind="warning"] p,
[data-baseweb="notification"][kind="warning"] span,
[data-baseweb="notification"][kind="warning"] div {
    color: #fbbf24 !important;
}
/* ℹ️ Info — blue */
[data-baseweb="notification"][kind="info"] {
    background: #00102a !important;
    border-color: #001840 !important;
    border-left-color: #3b82f6 !important;
}
[data-baseweb="notification"][kind="info"] p,
[data-baseweb="notification"][kind="info"] span,
[data-baseweb="notification"][kind="info"] div {
    color: #93c5fd !important;
}
/* ✅ Success — emerald */
[data-baseweb="notification"][kind="positive"] {
    background: #001810 !important;
    border-color: #002218 !important;
    border-left-color: #10b981 !important;
}
[data-baseweb="notification"][kind="positive"] p,
[data-baseweb="notification"][kind="positive"] span,
[data-baseweb="notification"][kind="positive"] div {
    color: #6ee7b7 !important;
}
/* ❌ Error — rose */
[data-baseweb="notification"][kind="negative"] {
    background: #1a0010 !important;
    border-color: #280018 !important;
    border-left-color: #ef4444 !important;
}
[data-baseweb="notification"][kind="negative"] p,
[data-baseweb="notification"][kind="negative"] span,
[data-baseweb="notification"][kind="negative"] div {
    color: #fca5a5 !important;
}

/* ── Primary button ───────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px !important;
    box-shadow: 0 4px 18px rgba(139,92,246,0.40) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(139,92,246,0.55) !important;
}
.stButton > button[kind="primary"]:active {
    transform: translateY(0) !important;
}

/* ── Secondary / default button ──────────────────────────────────── */
.stButton > button[kind="secondary"],
.stButton > button:not([kind="primary"]) {
    background: #16161e !important;
    border: 1.5px solid #2e2e45 !important;
    border-radius: 10px !important;
    color: #a78bfa !important;
    font-weight: 500 !important;
    transition: background 0.15s, border-color 0.15s, color 0.15s !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind="primary"]):hover {
    background: #1e1e2e !important;
    border-color: #8b5cf6 !important;
    color: #c4b5fd !important;
}

/* ── Download button ─────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: #16161e !important;
    border: 1.5px solid #2e2e45 !important;
    border-radius: 10px !important;
    color: #a78bfa !important;
    font-weight: 500 !important;
    transition: background 0.15s, border-color 0.15s !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #1e1e2e !important;
    border-color: #8b5cf6 !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #16161e !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-weight: 500 !important;
    color: #6b6890 !important;
    border: none !important;
    padding: 6px 16px !important;
    transition: background 0.15s, color 0.15s !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #a78bfa !important;
    background: rgba(139,92,246,0.10) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
    color: #fff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 12px rgba(139,92,246,0.45) !important;
}

/* ── Progress bar ─────────────────────────────────────────────────── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #8b5cf6 0%, #22d3ee 100%) !important;
    border-radius: 999px !important;
}
/* Track */
.stProgress > div > div > div {
    background: #1e1e2e !important;
    border-radius: 999px !important;
}

/* ── Metric widget ────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #16161e !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    border: 1px solid #252535 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.35) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    color: #a78bfa !important;
}
[data-testid="stMetricLabel"] {
    color: #6b6890 !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
}
[data-testid="stMetricDelta"] {
    color: #34d399 !important;
}

/* ── Chat messages ────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #16161e !important;
    border-radius: 14px !important;
    border: 1px solid #252535 !important;
    margin-bottom: 8px !important;
}
[data-testid="stChatMessage"] p {
    color: #c4c0d9 !important;
}

/* ── Chat input ───────────────────────────────────────────────────── */
[data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
    background: #16161e !important;
    color: #eeeaf8 !important;
}
[data-testid="stChatInput"] > div {
    border-radius: 14px !important;
    border: 1.5px solid #2e2e45 !important;
    background: #16161e !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.30) !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.18) !important;
}

/* ── Text input / textarea ────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #16161e !important;
    border: 1.5px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #eeeaf8 !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.15) !important;
    background: #1a1a28 !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label {
    color: #9890b8 !important;
    font-weight: 500 !important;
}

/* ── Selectbox ────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: #16161e !important;
    border: 1.5px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #eeeaf8 !important;
}

/* ── Checkbox ─────────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label {
    font-weight: 500 !important;
    color: #c4c0d9 !important;
}

/* ── Containers with border ───────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #16161e !important;
    border-radius: 14px !important;
    border: 1px solid #252535 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
}

/* ── Divider ──────────────────────────────────────────────────────── */
hr {
    border-color: #252535 !important;
    margin: 12px 0 !important;
}

/* ── Headings ─────────────────────────────────────────────────────── */
h1 {
    background: linear-gradient(135deg, #a78bfa 0%, #22d3ee 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 900 !important;
    letter-spacing: -0.8px !important;
}
h2 { color: #c4b5fd !important; font-weight: 700 !important; }
h3 { color: #a78bfa !important; font-weight: 600 !important; }
h4, h5, h6 { color: #9b87d1 !important; }

/* ── Expander ─────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #16161e !important;
    border-radius: 10px !important;
    border: 1px solid #252535 !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #a78bfa !important;
    font-weight: 500 !important;
}

/* ── Code block ───────────────────────────────────────────────────── */
[data-testid="stCodeBlock"] {
    border-radius: 12px !important;
    background: #0a0a10 !important;
}
[data-testid="stCodeBlock"] pre {
    background: #0a0a10 !important;
}

/* ── Caption ──────────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #5c5877 !important;
}

/* ── Form submit button ───────────────────────────────────────────── */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 18px rgba(139,92,246,0.40) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(139,92,246,0.55) !important;
}

/* ── Custom scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0e0e13; }
::-webkit-scrollbar-thumb { background: #2e2e48; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #8b5cf6; }
</style>
""", unsafe_allow_html=True)

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
    st.markdown("**💾 数据备份**")
    st.caption("数据自动保存到本地文件，重启后自动恢复。")

    # 导出
    _all_json = json.dumps(
        dict(st.session_state.get("ideas", {})), ensure_ascii=False, indent=2
    )
    st.download_button(
        "📤 导出全部数据",
        data=_all_json,
        file_name="idea_backup.json",
        mime="application/json",
        use_container_width=True,
        help="下载 JSON 备份文件，可在其他设备导入恢复",
    )

    # 导入
    _uploaded = st.file_uploader(
        "📥 导入数据（.json）",
        type=["json"],
        help="选择之前导出的备份文件，数据将合并到当前列表",
        label_visibility="collapsed",
    )
    if _uploaded is not None:
        _import_key = f"imported_{_uploaded.name}_{_uploaded.size}"
        if not st.session_state.get(_import_key):
            try:
                _raw = json.loads(_uploaded.read().decode("utf-8"))
                if isinstance(_raw, dict):
                    st.session_state.setdefault("ideas", {}).update(_raw)
                    # 写入本地文件
                    try:
                        pathlib.Path(__file__).parent.joinpath("ideas_data.json").write_text(
                            json.dumps(dict(st.session_state["ideas"]), ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                    except Exception:
                        pass
                    st.session_state[_import_key] = True
                    st.success(f"✅ 已导入 {len(_raw)} 条数据")
                    st.rerun()
                else:
                    st.error("格式错误：文件内容应为 JSON 对象")
            except Exception as _e:
                st.error(f"导入失败：{_e}")

    st.markdown("---")
    st.caption("[📖 使用说明 & 源码](https://github.com/0000-huajiao/idea-analyzer)")


def is_configured() -> bool:
    return bool(st.session_state.get("cfg_key") and st.session_state.get("cfg_base"))


# ─── Constants ────────────────────────────────────────────────────────────────
MAX_RETRY     = 4
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
- completeness ≥ 85 时，不要将 question 设为 null，改为用一句话告知文档已较完整，然后开放式地问用户："还有什么想补充或调整的地方吗？"
- 若用户明确表示没有补充（如"没了"、"就这些"、"完成"、"够了"），再将 question 设为 null
- 若用户提出补充点，针对该点继续追问深入（最多 2-3 个追问），直到该点梳理清楚再回到开放式询问
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
- completeness ≥ 85 时，不要将 question 设为 null，改为用一句话告知蓝图已较完整，然后开放式地问用户："还有什么想补充的吗？比如某个人物细节、某段情节、或者结局的方向……"
- 若用户明确表示没有补充（如"没了"、"就这些"、"完成"、"够了"），再将 question 设为 null
- 若用户提出补充点，针对该点继续追问深入（最多 2-3 个追问），直到该点梳理清楚再回到开放式询问

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

def build_lit_system_prompt(lit_type: str = "", lit_subtype: str = "") -> str:
    """根据文学类型和子类型生成个性化系统提示。"""
    type_hints = {
        "novel": {
            "romance":  "重点关注主角之间的情感发展、误会与破冰、感情线节奏，情感描写要细腻真实。",
            "ensemble": "关注多主角视角切换、各角色弧光与交汇点，保持人物群像的立体感与差异性。",
            "mystery":  "关注谜题设置、线索布置、反转设计，确保伏笔合理、节奏紧凑、解谜令人信服。",
            "plot":     "关注事件驱动力、冲突升级节奏、核心矛盾的层层递进与最终解决。",
            "mixed":    "灵活融合多种叙事元素，兼顾情感、悬念、人物与情节的平衡。",
        },
        "script":  "关注场景切换、对白节奏、戏剧张力，注重舞台/镜头表达而非描写性文字。",
        "prose":   "关注散文的意境与情感流动，语言应自然舒展，善用具体细节触动读者。",
        "poem":    "关注意象选取、韵律节奏、情感浓缩，每个字词都应精炼有力。",
    }
    hint = ""
    if lit_type == "novel":
        hint = type_hints["novel"].get(lit_subtype, "关注人物塑造、情节发展与主题深度。")
    elif lit_type in type_hints:
        hint = type_hints[lit_type]
    if hint:
        return LIT_PROMPT + f"\n\n【本次创作重点】{hint}"
    return LIT_PROMPT

COMPETITOR_PROMPT = """你是一位市场研究专家。根据产品PRD分析竞品（如启用联网则基于实时搜索，否则基于训练知识）。

只输出合法 JSON：
{
  "summary": "市场概况（2-3句）",
  "competitors": [{"name":"竞品名","description":"一句话描述","strengths":["优势"],"weaknesses":["劣势"],"url":"官网或空字符串"}],
  "market_gap": "市场空白和机会点",
  "differentiation": "差异化建议",
  "feasibility": {"score": 1到10整数, "rationale": "可行性理由", "recommendations": ["行动建议"]}
}"""

WIREFRAME_PROMPT = """你是一位资深 UI/UX 设计师兼产品开发规格专家，根据 PRD 输出一份完整的「开发规格文档」，包含以下三部分，直接可以作为 AI 开发助手（Cursor / Claude / GPT-4）的输入。

════════════════════════════════════
## 一、核心页面 ASCII 线框图
════════════════════════════════════
为每个核心页面绘制 ASCII 线框图：
- 使用 +--+  |  [ ]  ( )  ###  ~~~  等字符表示 UI 元素（导航栏/按钮/输入框/卡片/列表/图片占位符等）
- 每个页面标注名称，线框图下方注明 1-2 句交互说明
- 结合 ui_style 中的风格与配色，在每张线框图旁注明色彩/字体建议
- 覆盖所有主流程的核心页面，不遗漏

════════════════════════════════════
## 二、业务流程泳道图（ASCII）
════════════════════════════════════
用 ASCII 泳道图展示核心业务主流程，各列代表不同角色（如：用户 / 前端 / 后端 / 第三方服务），各行代表操作步骤：

示例格式：
┌─────────────┬─────────────────────┬─────────────────────┬────────────────┐
│    用户      │       前端           │       后端           │  第三方服务    │
├─────────────┼─────────────────────┼─────────────────────┼────────────────┤
│ 点击登录     │ 显示登录表单         │                     │                │
│ 填写账号密码  │ 格式校验             │                     │                │
│             │ POST /api/login ──► │ 验证账号密码         │                │
│             │                     │ ──► 签发 JWT Token  │                │
│ 进入主界面   │ ◄── 返回 Token      │                     │                │
└─────────────┴─────────────────────┴─────────────────────┴────────────────┘

根据产品实际角色和流程绘制，确保泳道清晰准确。

════════════════════════════════════
## 三、功能详细开发规格
════════════════════════════════════
为每个核心功能模块输出详细规格，包含：
- 功能概述（1-2句）
- 建议技术实现（技术栈/核心接口路径/关键数据结构）
- 交互细节与边界条件
- 异常处理与降级策略

格式清晰，措辞精确，可直接作为 AI 开发提示词。

只输出文档正文，不含JSON，不含多余解释。"""

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
                wait = 15 * (attempt + 1)   # 15s → 30s → 45s，给 Burst 限速足够缓冲
                time.sleep(wait)
        except openai.APIError as e:
            last_err = e
            if attempt < MAX_RETRY - 1:
                time.sleep(5 * (attempt + 1))
    raise last_err or RuntimeError("API 调用失败")

_MIN_REQUEST_INTERVAL = 4   # 两次请求之间最少间隔秒数，防止 Burst

def _enforce_rate_limit():
    """强制最小请求间隔，避免连续请求触发 Burst 保护。"""
    last = st.session_state.get("_last_api_call_time", 0.0)
    elapsed = time.time() - last
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    st.session_state["_last_api_call_time"] = time.time()

def _call_with_retry(sys_msgs: list, all_msgs: list, thinking_ph) -> str:
    """
    保持完整上下文重试：429 时只等待更长时间，不裁剪历史消息。
    sys_msgs   : 系统消息列表
    all_msgs   : 完整对话历史（最新在后）
    thinking_ph: st.empty() 占位符，用于显示重试状态
    """
    history  = all_msgs[-HISTORY_LIMIT:]
    api_msgs = sys_msgs + [{"role": m["role"], "content": m["content"]} for m in history]
    waits    = [60, 120, 180]   # 429 时的等待梯度（秒）
    last_err = None

    _enforce_rate_limit()   # 请求前确保间隔

    for attempt in range(len(waits) + 1):
        try:
            full_text = ""
            for chunk in call_api_streaming(api_msgs):
                full_text += chunk
            return full_text                              # 流式成功
        except openai.RateLimitError as e:
            last_err = e
            if attempt < len(waits):
                wait = waits[attempt]
                thinking_ph.markdown(
                    f"⏳ 请求频率超限，等待 {wait}s 后重试"
                    f"（第 {attempt + 1}/{len(waits)} 次，保持完整上下文）…"
                )
                time.sleep(wait)
                st.session_state["_last_api_call_time"] = time.time()
            else:
                raise
        except Exception:
            # 非限速错误：降级到非流式
            _enforce_rate_limit()
            return call_api(api_msgs)

    raise last_err or RuntimeError("API 调用失败")

def call_api_streaming(messages: list):
    """简单流式调用，不含重试逻辑，异常直接抛出由外层处理。"""
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
                # 429 Burst 限速需要更长等待
                wait = 15 * (attempt + 1) if "429" in str(e) or "TooManyRequests" in str(e) else 5 * (attempt + 1)
                time.sleep(wait)
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
    # HTML-escape for safe embedding inside <div> (& and < are the critical ones)
    code_html = code.replace("&", "&amp;").replace("<", "&lt;")
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  body{{margin:0;padding:10px;background:#16161e;font-family:sans-serif;}}
  #err{{color:#f87171;font-size:12px;padding:4px;}}
  svg{{max-width:100%;height:auto;border-radius:8px;}}
</style>
</head><body>
<div class="mermaid">{code_html}</div>
<div id="err"></div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
  onerror="document.getElementById('err').textContent='CDN加载失败，请检查网络'"></script>
<script>
try {{
  mermaid.initialize({{
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    flowchart: {{ curve: 'linear', useMaxWidth: true }},
    themeVariables: {{
      primaryColor: '#8b5cf6', primaryTextColor: '#eeeaf8', primaryBorderColor: '#6d28d9',
      lineColor: '#a78bfa', secondaryColor: '#1e1e2e', tertiaryColor: '#16161e',
      edgeLabelBackground: '#1e1e2e', clusterBkg: '#1c1c28',
      titleColor: '#c4b5fd', nodeTextColor: '#eeeaf8'
    }}
  }});
  mermaid.run({{querySelector: '.mermaid'}}).catch(function(e) {{
    document.getElementById('err').textContent = '渲染错误: ' + e.message;
  }});
}} catch(e) {{
  document.getElementById('err').textContent = '初始化错误: ' + e.message;
}}
</script></body></html>"""
    st.components.v1.html(html, height=height, scrolling=True)
    with st.expander("📋 Mermaid 源码（可复制到 mermaid.live 预览）"):
        st.code(code, language="text")

# ─── Session-based idea storage ───────────────────────────────────────────────
DATA_FILE = pathlib.Path(__file__).parent / "ideas_data.json"

def ss_ideas() -> dict:
    if "ideas" not in st.session_state:
        st.session_state.ideas = {}
    return st.session_state.ideas

def _persist_all():
    """将所有 idea 写入本地 JSON 文件。"""
    try:
        DATA_FILE.write_text(
            json.dumps(dict(ss_ideas()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

def _load_local_data():
    """启动后首次从本地文件加载数据（每个 session 只加载一次）。"""
    if st.session_state.get("_data_loaded"):
        return
    st.session_state["_data_loaded"] = True
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                ss_ideas().update(raw)
        except Exception:
            pass

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
    _persist_all()

def delete_idea(idea_id: str):
    ss_ideas().pop(idea_id, None)
    _persist_all()

def _next_version_name(idea: dict) -> str:
    """根据现有版本自动推算下一个版本号。"""
    versions = idea.get("versions", [])
    if not versions:
        return "v1.0"
    last = versions[-1]["version"]  # e.g. "v1.2"
    try:
        major, minor = last.lstrip("v").split(".")
        return f"v{major}.{int(minor) + 1}"
    except Exception:
        return f"v{len(versions) + 1}.0"

def _get_new_modules(idea: dict) -> list[str]:
    """对比上一个版本，返回当前新增的功能模块名列表。"""
    versions = idea.get("versions", [])
    if not versions:
        return []
    prev_modules = {m.get("module", "") for m in versions[-1].get("prd", {}).get("functional_req", [])}
    curr_modules  = [m.get("module", "") for m in idea.get("prd", {}).get("functional_req", [])
                     if m.get("module") and m.get("module") not in prev_modules]
    return curr_modules

def _save_version(idea: dict, version_name: str, label: str = ""):
    """将当前 PRD/流程图/规格 快照为一个版本并追加到 versions 列表。"""
    new_modules = _get_new_modules(idea)
    snapshot = {
        "version":     version_name,
        "label":       label,
        "created_at":  datetime.now().isoformat(),
        "prd":         json.loads(json.dumps(idea.get("prd", {}),      ensure_ascii=False)),
        "flowchart":   idea.get("flowchart", ""),
        "ai_prompt":   idea.get("ai_prompt", ""),
        "completeness": idea.get("completeness", 0),
        "new_modules": new_modules,
    }
    idea.setdefault("versions", []).append(snapshot)

def empty_prd() -> dict:
    return {k: ([] if k in LIST_FIELDS | FEATURE_FIELDS else "") for k, _ in PRD_MODULES}

def new_idea(title: str, idea_type: str = "product") -> dict:
    return {
        "id":                    uuid.uuid4().hex[:8],
        "title":                 title,
        "idea_type":             idea_type,
        "lit_type":              "",   # "novel" | "script" | "prose" | "poem"
        "lit_subtype":           "",   # "romance"|"ensemble"|"mystery"|"plot"|"mixed"（仅novel）
        "created_at":            datetime.now().isoformat(),
        "updated_at":            datetime.now().isoformat(),
        "messages":              [],
        "prd":                   empty_prd(),
        "flowchart":             "",
        "competitor_analysis":   {},
        "ai_prompt":             "",
        "test_cases":            {},
        "outline":               {"character_relationships": []},
        "completeness":          0,
        "milestones_celebrated": [],
        "versions":              [],  # [{version, label, created_at, prd, flowchart, ai_prompt, completeness, new_modules}]
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
        rels = outline.get("character_relationships", [])
        if rels:
            out.append("## 人物关系\n")
            out.append("| 人物A | 关系 | 人物B | 描述 |")
            out.append("|------|------|------|------|")
            for r in rels:
                out.append(f"| {r.get('from','')} | {r.get('type','')} | {r.get('to','')} | {r.get('desc','')} |")
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

# ─── Multi-format export helpers ──────────────────────────────────────────────
def _inline_md_to_html(text: str) -> str:
    """Convert inline Markdown to HTML, with HTML escaping."""
    import html as _html
    text = _html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text

def _md_to_html(md_text: str, title: str) -> str:
    """Convert Markdown to a styled, self-contained HTML document (printable as PDF)."""
    lines = md_text.split('\n')
    body  = []
    i     = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('### '):
            body.append(f'<h3>{_inline_md_to_html(line[4:])}</h3>')
        elif line.startswith('## '):
            body.append(f'<h2>{_inline_md_to_html(line[3:])}</h2>')
        elif line.startswith('# '):
            body.append(f'<h1>{_inline_md_to_html(line[2:])}</h1>')
        elif line.strip() == '---':
            body.append('<hr>')
        elif line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            is_sep = lambda s: all(re.match(r'^[-:]+$', c.strip()) for c in s.split('|')[1:-1] if c.strip())
            if next_line.startswith('|') and is_sep(next_line):
                # Header row → table
                body.append('<table><thead><tr>' +
                            ''.join(f'<th>{_inline_md_to_html(c)}</th>' for c in cells) +
                            '</tr></thead><tbody>')
                i += 2
                while i < len(lines) and lines[i].startswith('|'):
                    rc = [c.strip() for c in lines[i].split('|')[1:-1]]
                    body.append('<tr>' + ''.join(f'<td>{_inline_md_to_html(c)}</td>' for c in rc) + '</tr>')
                    i += 1
                body.append('</tbody></table>')
                continue
            elif is_sep(line):
                pass  # stray separator
            else:
                body.append('<tr>' + ''.join(f'<td>{_inline_md_to_html(c)}</td>' for c in cells) + '</tr>')
        elif re.match(r'^\d+\. ', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                item_text = re.sub(r'^\d+\. ', '', lines[i])
                items.append('<li>' + _inline_md_to_html(item_text) + '</li>')
                i += 1
            body.append('<ol>' + ''.join(items) + '</ol>')
            continue
        elif line.startswith('- ') or line.startswith('* '):
            items = []
            while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('* ')):
                items.append(f'<li>{_inline_md_to_html(lines[i][2:])}</li>')
                i += 1
            body.append('<ul>' + ''.join(items) + '</ul>')
            continue
        elif line.strip():
            body.append(f'<p>{_inline_md_to_html(line)}</p>')
        i += 1

    body_html = '\n'.join(body)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    return f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8">
<title>{title}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
     max-width:900px;margin:40px auto;padding:0 24px;color:#1a1a2e;line-height:1.8;}}
h1{{color:#4c1d95;border-bottom:3px solid #8b5cf6;padding-bottom:10px;margin-top:40px;font-size:1.8rem;}}
h2{{color:#5b21b6;border-left:4px solid #8b5cf6;padding-left:12px;margin-top:32px;font-size:1.3rem;}}
h3{{color:#6d28d9;margin-top:20px;font-size:1.1rem;}}
table{{border-collapse:collapse;width:100%;margin:16px 0;font-size:.9rem;}}
th{{background:#8b5cf6;color:#fff;padding:9px 14px;text-align:left;}}
td{{border:1px solid #ddd;padding:7px 14px;}}
tr:nth-child(even){{background:#f5f3ff;}}
hr{{border:none;border-top:1px solid #e0e0e0;margin:24px 0;}}
code{{background:#f5f3ff;color:#6d28d9;padding:2px 6px;border-radius:4px;font-family:monospace;}}
ol,ul{{padding-left:24px;}}li{{margin:4px 0;}}
strong{{color:#3b0764;}}
.footer{{text-align:center;color:#999;font-size:12px;margin-top:60px;
         border-top:1px solid #eee;padding-top:16px;}}
@media print{{body{{max-width:100%;margin:20px;}}}}
</style></head><body>
{body_html}
<div class="footer">由 Idea 需求分析器 生成 · {ts}</div>
</body></html>"""

def _inline_md_to_confluence(text: str) -> str:
    """Convert inline Markdown to Confluence Wiki Markup."""
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
    text = re.sub(r'`(.+?)`', r'{{\1}}', text)
    return text

def _md_to_confluence(md_text: str) -> str:
    """Convert Markdown to Confluence Wiki Markup."""
    lines = md_text.split('\n')
    out   = []
    i     = 0
    is_sep = lambda s: s.startswith('|') and all(re.match(r'^[-:]+$', c.strip())
                        for c in s.split('|')[1:-1] if c.strip())
    while i < len(lines):
        line = lines[i]
        if line.startswith('### '):
            out.append('h3. ' + line[4:])
        elif line.startswith('## '):
            out.append('h2. ' + line[3:])
        elif line.startswith('# '):
            out.append('h1. ' + line[2:])
        elif line.strip() == '---':
            out.append('----')
        elif line.startswith('|'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if next_line and is_sep(next_line):
                out.append('||' + '||'.join(_inline_md_to_confluence(c) for c in cells) + '||')
                i += 2
                while i < len(lines) and lines[i].startswith('|') and not is_sep(lines[i]):
                    rc = [c.strip() for c in lines[i].split('|')[1:-1]]
                    out.append('|' + '|'.join(_inline_md_to_confluence(c) for c in rc) + '|')
                    i += 1
                continue
            elif is_sep(line):
                pass
            else:
                out.append('|' + '|'.join(_inline_md_to_confluence(c) for c in cells) + '|')
        elif re.match(r'^\d+\. ', line):
            out.append('# ' + _inline_md_to_confluence(re.sub(r'^\d+\. ', '', line)))
        elif line.startswith('- ') or line.startswith('* '):
            out.append('* ' + _inline_md_to_confluence(line[2:]))
        else:
            out.append(_inline_md_to_confluence(line))
        i += 1
    return '\n'.join(out)

def prd_to_html(idea: dict) -> str:
    title = idea.get("title", "需求文档")
    md = (f"# {title} — 产品需求文档\n\n"
          f"_生成于：{datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n---\n\n"
          + prd_to_md(idea.get("prd", {}), full=True))
    return _md_to_html(md, f"{title} PRD")

def prd_to_confluence_wiki(idea: dict) -> str:
    title = idea.get("title", "需求文档")
    md = (f"# {title} — 产品需求文档\n\n"
          f"_生成于：{datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n---\n\n"
          + prd_to_md(idea.get("prd", {}), full=True))
    return _md_to_confluence(md)

def lit_to_html(idea: dict) -> str:
    return _md_to_html(lit_export_md(idea), f"{idea.get('title', '创作蓝图')} 创作蓝图")

def lit_to_confluence_wiki(idea: dict) -> str:
    return _md_to_confluence(lit_export_md(idea))

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

_load_local_data()   # 每个 session 只执行一次，从本地文件恢复数据

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
        st.session_state.lit_type      = ""
        st.session_state.lit_subtype   = ""
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

    itype = st.session_state.new_idea_type

    # Step 2: 文学创作细分类型
    if itype == "literature" and not st.session_state.get("lit_type"):
        st.subheader("选择创作类型")
        st.markdown("你想写哪种类型的文学作品？")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            with st.container(border=True):
                st.markdown("### 📚 小说")
                st.caption("虚构叙事，人物驱动")
                if st.button("选择 小说 →", use_container_width=True):
                    st.session_state.lit_type = "novel"
                    st.rerun()
        with col2:
            with st.container(border=True):
                st.markdown("### 🎭 剧本")
                st.caption("对白+场景，戏剧张力")
                if st.button("选择 剧本 →", use_container_width=True):
                    st.session_state.lit_type = "script"
                    st.rerun()
        with col3:
            with st.container(border=True):
                st.markdown("### 🌿 散文随笔")
                st.caption("抒情叙事，自由表达")
                if st.button("选择 散文 →", use_container_width=True):
                    st.session_state.lit_type = "prose"
                    st.rerun()
        with col4:
            with st.container(border=True):
                st.markdown("### 🎵 诗歌")
                st.caption("意象凝练，韵律节奏")
                if st.button("选择 诗歌 →", use_container_width=True):
                    st.session_state.lit_type = "poem"
                    st.rerun()
        return

    # Step 3: 小说子类型
    if itype == "literature" and st.session_state.get("lit_type") == "novel" and not st.session_state.get("lit_subtype"):
        st.subheader("选择小说类型")
        st.caption("已选择：📚 小说")
        st.markdown("小说的主要风格是？")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            with st.container(border=True):
                st.markdown("### 💕 言情")
                st.caption("情感发展与羁绊")
                if st.button("选择 言情 →", use_container_width=True):
                    st.session_state.lit_subtype = "romance"
                    st.rerun()
        with col2:
            with st.container(border=True):
                st.markdown("### 👥 群像")
                st.caption("多主角视角切换")
                if st.button("选择 群像 →", use_container_width=True):
                    st.session_state.lit_subtype = "ensemble"
                    st.rerun()
        with col3:
            with st.container(border=True):
                st.markdown("### 🔍 悬疑")
                st.caption("谜题线索与反转")
                if st.button("选择 悬疑 →", use_container_width=True):
                    st.session_state.lit_subtype = "mystery"
                    st.rerun()
        with col4:
            with st.container(border=True):
                st.markdown("### ⚔️ 剧情")
                st.caption("事件驱动与冲突")
                if st.button("选择 剧情 →", use_container_width=True):
                    st.session_state.lit_subtype = "plot"
                    st.rerun()
        with col5:
            with st.container(border=True):
                st.markdown("### 🌈 混合")
                st.caption("多类型融合")
                if st.button("选择 混合 →", use_container_width=True):
                    st.session_state.lit_subtype = "mixed"
                    st.rerun()
        return

    # Step 4: 填写描述
    type_label = "📦 产品需求" if itype == "product" else "✍️ 文学创作"
    lit_type_labels = {"novel": "📚 小说", "script": "🎭 剧本", "prose": "🌿 散文随笔", "poem": "🎵 诗歌"}
    lit_subtype_labels = {"romance": "💕 言情", "ensemble": "👥 群像", "mystery": "🔍 悬疑", "plot": "⚔️ 剧情", "mixed": "🌈 混合"}
    if itype == "literature":
        lt  = st.session_state.get("lit_type", "")
        lst = st.session_state.get("lit_subtype", "")
        label_parts = [type_label, lit_type_labels.get(lt, "")]
        if lst:
            label_parts.append(lit_subtype_labels.get(lst, ""))
        st.caption(f"已选择：{'  ›  '.join(p for p in label_parts if p)}")
    else:
        st.caption(f"已选择：{type_label}")

    placeholder = (
        "例如：我想做一款帮助大学生找兼职的App…"
        if itype == "product"
        else "例如：我想写一个关于末日后人类重建文明的故事…"
    )
    form_label = "✏️ 用自己的话描述你的想法：" if itype == "product" else "✏️ 简单描述你的故事 idea："

    with st.form("new_form", clear_on_submit=True):
        idea_text = st.text_area(form_label, placeholder=placeholder, height=160,
                                 help="不需要很完整，一两句话就行，AI会引导你深入挖掘")
        go = st.form_submit_button("🚀 开始梳理", type="primary", use_container_width=True)

    if go and idea_text.strip():
        raw_title = idea_text.strip()
        title     = (raw_title[:18] + "…") if len(raw_title) > 18 else raw_title
        d         = new_idea(title, idea_type=itype)
        if itype == "literature":
            d["lit_type"]    = st.session_state.get("lit_type", "")
            d["lit_subtype"] = st.session_state.get("lit_subtype", "")
        prefix    = "我的产品想法是：" if itype == "product" else "我的故事想法是："
        d["messages"].append({"role": "user", "content": f"{prefix}{raw_title}"})
        save_idea(d)
        st.session_state.idea          = d
        st.session_state.edit_mode     = False
        st.session_state.processing    = True
        st.session_state.new_milestone = 0
        st.session_state.stage3_choice = ""
        st.session_state.new_idea_type = ""
        st.session_state.lit_type      = ""
        st.session_state.lit_subtype   = ""
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

    st.info("人物档案请在「👤 人物档案」Tab 中编辑。")

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
        (bool(idea.get("ai_prompt")),           "📐 开发规格文档"),
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
    if idea.get("completeness", 0) >= 85 and not st.session_state.get("new_milestone"):
        st.success("🎉 需求梳理完成！右侧各 Tab 可查看/导出所有产出。")

    left, mid, right = st.columns([4, 2, 5], gap="medium")

    with mid:
        render_progress_panel(idea)

    with right:
        tab_prd, tab_flow, tab_comp, tab_wire, tab_test, tab_ver = st.tabs(
            ["📋 需求文档", "🗺️ 流程图", "🔍 竞品分析", "📐 开发规格", "🧪 测试用例", "🕰️ 版本历史"]
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
                st.download_button("📄 导出 Markdown", data=prd_to_md(idea.get("prd", {}), full=True),
                                   file_name=f"{idea['title']}_PRD.md", mime="text/markdown",
                                   use_container_width=True)
            with st.expander("🔄 更多导出格式"):
                _etitle = idea.get("title", "需求文档")
                _ec1, _ec2 = st.columns(2)
                with _ec1:
                    st.download_button("🖨️ HTML（可打印为PDF）", data=prd_to_html(idea),
                                       file_name=f"{_etitle}_PRD.html", mime="text/html",
                                       use_container_width=True, key="prd_dl_html")
                with _ec2:
                    st.download_button("🔷 Confluence Wiki (.txt)", data=prd_to_confluence_wiki(idea),
                                       file_name=f"{_etitle}_PRD_confluence.txt", mime="text/plain",
                                       use_container_width=True, key="prd_dl_conf")
                st.caption("HTML：用浏览器打开后 Ctrl+P 另存为 PDF　|　Confluence：粘贴到页面编辑器 Wiki 标记模式　|　Notion：直接导入上方 Markdown 文件")
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
            st.caption("包含：ASCII页面线框图 · 业务流程泳道图 · 功能详细开发规格，可直接喂给 AI 构建产品")
            if st.button("📐 生成完整开发规格文档", type="primary", use_container_width=True):
                _save_version_dialog(idea)
            if st.session_state.prompt_loading:
                with st.spinner("AI 正在生成开发规格文档（线框图 + 泳道图 + 功能规格，约60秒）..."):
                    wf = gen_wireframe(idea)
                    if wf:
                        idea["ai_prompt"] = wf
                        save_idea(idea)
                st.session_state.prompt_loading = False
                st.rerun()
            if idea.get("ai_prompt"):
                st.download_button("📥 下载开发规格文档", data=idea["ai_prompt"],
                                   file_name=f"{idea['title']}_开发规格.txt",
                                   mime="text/plain", use_container_width=True)
                st.code(idea["ai_prompt"], language="text")
            else:
                st.info("需求梳理完成后点击上方按钮，AI 将生成包含 ASCII 线框图、业务泳道图和功能规格的完整开发文档。")

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

        with tab_ver:
            versions = idea.get("versions", [])
            if not versions:
                st.info("还没有保存过版本。生成开发规格文档时系统会提示你保存版本快照。")
            else:
                st.caption(f"共 {len(versions)} 个版本，点击「恢复」可将 PRD 回退到该版本。")
                for i, v in enumerate(reversed(versions)):
                    real_idx = len(versions) - 1 - i
                    with st.container(border=True):
                        vc1, vc2 = st.columns([7, 3])
                        with vc1:
                            is_latest = (real_idx == len(versions) - 1)
                            badge = " 🟢 最新" if is_latest else ""
                            st.markdown(f"**{v['version']}**{badge}　{v.get('label', '')}")
                            st.caption(datetime.fromisoformat(v["created_at"]).strftime("%Y-%m-%d %H:%M")
                                       + f"　完整度：{v.get('completeness', 0)}%")
                            new_mods = v.get("new_modules", [])
                            if new_mods:
                                st.markdown("🆕 **新增模块：** " + "、".join(new_mods))
                        with vc2:
                            if not is_latest:
                                if st.button("⏪ 恢复此版本", key=f"ver_restore_{real_idx}",
                                             use_container_width=True):
                                    # 恢复 prd / flowchart / ai_prompt / completeness
                                    idea["prd"]          = json.loads(json.dumps(v["prd"], ensure_ascii=False))
                                    idea["flowchart"]    = v.get("flowchart", "")
                                    idea["ai_prompt"]    = v.get("ai_prompt", "")
                                    idea["completeness"] = v.get("completeness", 0)
                                    save_idea(idea)
                                    st.toast(f"已恢复到 {v['version']} ✓")
                                    st.rerun()
                            else:
                                st.caption("（当前版本）")
                # 手动存版本
                st.markdown("---")
                if st.button("💾 手动保存当前版本", use_container_width=True):
                    _save_version_dialog(idea)

    with left:
        _chat_product(idea)

# ─── Character profiles tab（文学模式）────────────────────────────────────────
def render_character_profiles(idea: dict):
    outline = idea.get("outline") or {}
    chars   = outline.get("characters") or []
    iid     = idea["id"]

    # edit state: -1=none, -2=new, >=0=editing index
    edit_idx = st.session_state.get(f"char_edit_idx_{iid}", -1)

    if edit_idx == -1:
        # Display cards
        if not chars:
            st.info("还没有人物档案。点击下方「＋ 添加人物」开始创建。")
        for i, c in enumerate(chars):
            with st.container(border=True):
                hcol1, hcol2 = st.columns([8, 2])
                with hcol1:
                    st.markdown(f"### {c.get('name', '（无名）')}")
                with hcol2:
                    ecol, dcol = st.columns(2)
                    with ecol:
                        if st.button("✏️", key=f"char_edit_{iid}_{i}", help="编辑"):
                            st.session_state[f"char_edit_idx_{iid}"] = i
                            st.rerun()
                    with dcol:
                        if st.button("🗑️", key=f"char_del_{iid}_{i}", help="删除"):
                            chars.pop(i)
                            outline["characters"] = chars
                            idea["outline"]       = outline
                            save_idea(idea)
                            st.rerun()
                if c.get("role"):        st.markdown(f"**角色定位：** {c['role']}")
                if c.get("personality"): st.markdown(f"**性格特征：** {c['personality']}")
                if c.get("arc"):         st.markdown(f"**人物弧光：** {c['arc']}")

        st.markdown("")
        if st.button("＋ 添加人物", type="primary"):
            st.session_state[f"char_edit_idx_{iid}"] = -2
            st.rerun()
    else:
        # Edit / new form
        is_new = (edit_idx == -2)
        st.subheader("新增人物" if is_new else "编辑人物")
        default = {} if is_new else chars[edit_idx]
        name        = st.text_input("姓名",     value=default.get("name", ""),        key=f"char_f_name_{iid}")
        role        = st.text_input("角色定位", value=default.get("role", ""),        key=f"char_f_role_{iid}")
        personality = st.text_input("性格特征", value=default.get("personality", ""), key=f"char_f_pers_{iid}")
        arc         = st.text_area("人物弧光",  value=default.get("arc", ""),  height=80, key=f"char_f_arc_{iid}")

        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("💾 保存", type="primary", use_container_width=True):
                entry = {"name": name, "role": role, "personality": personality, "arc": arc}
                if is_new:
                    chars.append(entry)
                else:
                    chars[edit_idx] = entry
                outline["characters"] = chars
                idea["outline"]       = outline
                save_idea(idea)
                st.session_state[f"char_edit_idx_{iid}"] = -1
                st.rerun()
        with sc2:
            if st.button("取消", use_container_width=True):
                st.session_state[f"char_edit_idx_{iid}"] = -1
                st.rerun()


# ─── Relationship network tab（文学模式）────────────────────────────────────
def render_relationship_network(idea: dict):
    import streamlit.components.v1 as components
    outline = idea.get("outline") or {}
    chars   = outline.get("characters") or []
    rels    = outline.get("character_relationships") or []
    iid     = idea["id"]

    # ── vis.js graph ──
    if not chars:
        st.info("先在「👤 人物档案」Tab 添加人物，关系图谱将在这里显示。")
    else:
        nodes_js = json.dumps(
            [{"id": c.get("name",""), "label": c.get("name","")} for c in chars if c.get("name")],
            ensure_ascii=False,
        )
        edges_js = json.dumps(
            [{"from": r.get("from",""), "to": r.get("to",""),
              "label": r.get("type",""), "title": r.get("desc","")} for r in rels],
            ensure_ascii=False,
        )
        html = f"""
<!DOCTYPE html><html><head>
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin:0; background:#16161e; }}
  #net {{ width:100%; height:390px; }}
</style>
</head><body>
<div id="net"></div>
<script>
  var nodes = new vis.DataSet({nodes_js});
  var edges = new vis.DataSet({edges_js});
  var options = {{
    nodes: {{
      color: {{ background:"#8b5cf6", border:"#6d28d9", highlight:{{background:"#a78bfa",border:"#8b5cf6"}} }},
      font:  {{ color:"#eeeaf8", size:14 }},
      shape: "dot", size:18
    }},
    edges: {{
      color: {{ color:"#a78bfa", highlight:"#c4b5fd" }},
      font:  {{ color:"#c4c0d9", size:12, align:"middle" }},
      arrows: {{ to:{{ enabled:false }} }},
      smooth: {{ type:"curvedCW", roundness:0.2 }}
    }},
    physics: {{ stabilization:{{ iterations:150 }} }},
    background: {{ color:"#16161e" }}
  }};
  new vis.Network(document.getElementById("net"), {{nodes,edges}}, options);
</script>
</body></html>
"""
        components.html(html, height=400)

    # ── Relationship table (inline editable) ──
    st.markdown("---")
    st.caption("点击单元格可直接编辑；末列「✕」删除行；底部「＋」新增行")

    import pandas as pd
    char_names = [c.get("name", "") for c in chars if c.get("name")]
    _rel_df = pd.DataFrame([{
        "人物A": r.get("from", ""), "关系类型": r.get("type", ""),
        "人物B": r.get("to", ""),   "描述":    r.get("desc", "")
    } for r in rels]) if rels else pd.DataFrame(columns=["人物A", "关系类型", "人物B", "描述"])

    # 版本号换 key，rerun 后旧 key 不存在 → 不会再次触发保存
    _rel_ver     = st.session_state.get(f"rel_ver_{iid}", 0)
    _editor_key  = f"rel_editor_{iid}_v{_rel_ver}"
    _edited_df   = st.data_editor(
        _rel_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "人物A":   st.column_config.SelectboxColumn("人物A",   options=char_names, width="small"),
            "人物B":   st.column_config.SelectboxColumn("人物B",   options=char_names, width="small"),
            "关系类型": st.column_config.TextColumn("关系类型", width="small"),
            "描述":    st.column_config.TextColumn("描述",     width="medium"),
        },
        key=_editor_key,
    )
    _estate = st.session_state.get(_editor_key, {})
    if _estate.get("edited_rows") or _estate.get("added_rows") or _estate.get("deleted_rows"):
        _new_rels = []
        for _, row in _edited_df.iterrows():
            _fc = str(row.get("人物A", "") or "").strip()
            _tc = str(row.get("人物B", "") or "").strip()
            if _fc and _tc:
                _new_rels.append({
                    "from": _fc,
                    "type": str(row.get("关系类型", "") or "").strip(),
                    "to":   _tc,
                    "desc": str(row.get("描述", "") or "").strip(),
                })
        outline["character_relationships"] = _new_rels
        idea["outline"] = outline
        save_idea(idea)
        st.session_state[f"rel_ver_{iid}"] = _rel_ver + 1  # 换 key，打破循环
        st.toast("关系已更新 ✓")
        st.rerun()


# ─── Literature mode workspace ────────────────────────────────────────────────
def _workspace_literature(idea: dict):
    if idea.get("completeness", 0) >= 85 and not st.session_state.get("new_milestone"):
        st.success("🎉 创作蓝图梳理完成！右侧各 Tab 可查看/导出所有产出。")

    left, mid, right = st.columns([4, 2, 5], gap="medium")

    with mid:
        render_progress_panel_lit(idea)

    with right:
        tab_story, tab_chars, tab_rels, tab_plan, tab_refs, tab_export = st.tabs([
            "📖 故事大纲", "👤 人物档案", "🕸️ 关系网",
            "🗺️ 写作计划", "📚 参考资料", "📤 导出"
        ])

        with tab_story:
            b1, b2 = st.columns(2)
            _pending_key = f"lit_pending_sync_{idea['id']}"
            with b1:
                edit_lbl = "✅ 完成编辑" if st.session_state.edit_mode else "✏️ 手动编辑大纲"
                if st.button(edit_lbl, use_container_width=True, key="lit_edit_btn"):
                    if st.session_state.edit_mode:
                        old_outline = idea.pop("_edit_snapshot", {})
                        changed     = _compute_outline_diff(old_outline, idea.get("outline", {}))
                        if changed:
                            # 只保存，不自动触发 AI；把变更字段存起来等用户手动同步
                            st.session_state[_pending_key] = changed
                        save_idea(idea)
                        st.toast("保存成功 ✓ 如需通知AI同步，点击「同步到AI」")
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
            # 待同步提示 + 手动同步按钮
            if st.session_state.get(_pending_key) and not st.session_state.edit_mode:
                st.warning("大纲已修改，尚未通知 AI。")
                if st.button("🔄 同步变更到AI", type="primary", use_container_width=True, key="lit_sync_ai"):
                    _append_edit_notification(idea, st.session_state[_pending_key])
                    st.session_state.pop(_pending_key, None)
                    st.session_state.processing = True
                    st.rerun()
            if st.session_state.edit_mode:
                render_outline_editor(idea)
            else:
                md = outline_to_md(idea.get("outline", {}), section="story")
                if md.startswith("_大纲"):
                    st.info("对话开始后，故事大纲将在这里实时更新。")
                else:
                    st.markdown(md)

        with tab_chars:
            render_character_profiles(idea)

        with tab_rels:
            render_relationship_network(idea)

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
                "📥 导出 Markdown",
                data=lit_export_md(idea),
                file_name=f"{idea['title']}_创作蓝图.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True,
            )
            with st.expander("🔄 更多导出格式"):
                _ltitle = idea.get("title", "创作蓝图")
                _lc1, _lc2 = st.columns(2)
                with _lc1:
                    st.download_button("🖨️ HTML（可打印为PDF）", data=lit_to_html(idea),
                                       file_name=f"{_ltitle}_创作蓝图.html", mime="text/html",
                                       use_container_width=True, key="lit_dl_html")
                with _lc2:
                    st.download_button("🔷 Confluence Wiki (.txt)", data=lit_to_confluence_wiki(idea),
                                       file_name=f"{_ltitle}_创作蓝图_confluence.txt", mime="text/plain",
                                       use_container_width=True, key="lit_dl_conf")
                st.caption("HTML：用浏览器打开后 Ctrl+P 另存为 PDF　|　Confluence：粘贴到页面编辑器 Wiki 标记模式　|　Notion：直接导入上方 Markdown 文件")
            st.markdown("---")
            preview = outline_to_md(idea.get("outline", {}), section="full")
            if preview.startswith("_大纲"):
                st.info("对话完成后，完整创作蓝图将在这里预览。")
            else:
                st.markdown(preview)

    with left:
        _chat_literature(idea)

# ─── 版本存档弹窗 ───────────────────────────────────────────────────────────
@st.dialog("💾 是否保存当前版本？")
def _save_version_dialog(idea: dict):
    next_v = _next_version_name(idea)
    st.markdown(
        f"生成开发规格文档前，建议先将当前 PRD 存为一个版本快照，"
        f"方便后续迭代时对比和回退。"
    )
    version_name = st.text_input("版本号", value=next_v, key="dlg_ver_name")
    label        = st.text_input("版本说明（可选）", placeholder="如：初始版本 / 新增用户中心", key="dlg_ver_label")
    ca, cb = st.columns(2)
    with ca:
        if st.button("💾 保存并生成", type="primary", use_container_width=True):
            _save_version(idea, version_name.strip() or next_v, label.strip())
            save_idea(idea)
            st.session_state.prompt_loading = True
            st.rerun()
    with cb:
        if st.button("跳过，直接生成", use_container_width=True):
            st.session_state.prompt_loading = True
            st.rerun()

# ─── 产品模式三阶段完成弹窗 ───────────────────────────────────────────────────
@st.dialog("🎊 基础需求梳理完成！")
def _product_complete_dialog(idea: dict):
    st.balloons()
    st.markdown(
        "你已经把产品 **是什么、给谁用、怎么做** 都想清楚了！🎉\n\n"
        "现在可以：\n"
        "- **📐 生成开发规格文档** —— ASCII 线框图 + 泳道图 + 功能规格，直接喂给 AI 开始构建\n"
        "- **📋 导出完整 PRD** —— 标准13模块需求文档，发给团队或存档\n"
        "- **💪 继续深化** —— 补充非功能需求、业务规则、上线计划等细节"
    )
    st.markdown("---")

    prd_md = prd_to_md(idea.get("prd", {}), full=True)
    _dc1, _dc2 = st.columns(2)
    with _dc1:
        st.download_button(
            "📋 导出 Markdown PRD",
            data=prd_md,
            file_name=f"{idea['title']}_PRD.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with _dc2:
        st.download_button(
            "🖨️ 导出 HTML（可打印PDF）",
            data=prd_to_html(idea),
            file_name=f"{idea['title']}_PRD.html",
            mime="text/html",
            use_container_width=True,
        )

    ca, cb = st.columns(2)
    with ca:
        if st.button("📐 生成开发规格文档", type="primary", use_container_width=True,
                     key="dlg_gen_prompt"):
            st.session_state.new_milestone  = 0
            st.session_state.stage3_choice  = "prompt"
            st.session_state.prompt_loading = True
            st.rerun()
    with cb:
        if st.button("💪 继续深化细节", use_container_width=True,
                     key="dlg_continue"):
            st.session_state.new_milestone = 0
            st.session_state.stage3_choice = "continue"
            st.rerun()

# ─── 里程碑通知（对话历史正下方）─────────────────────────────────────────────
def _render_milestone_inline(idea: dict, stages: list, is_lit: bool = False):
    """渲染在对话历史的正下方，用户读完最新回答后立即看到。"""
    milestone = st.session_state.get("new_milestone", 0)
    if not milestone:
        return

    total    = len(stages)
    s_info   = stages[milestone - 1]
    is_final = (milestone >= total)

    if is_final:
        if is_lit:
            st.balloons()
            with st.container(border=True):
                st.success("🎊 **创作蓝图梳理完成！所有阶段全部达成！**")
                st.markdown("故事的世界观、人物、冲突、结构和写作计划都已理清楚了！")
                ca, cb = st.columns(2)
                with ca:
                    if st.button("📤 去导出创作蓝图", type="primary",
                                 use_container_width=True, key="ms_lit_export"):
                        st.session_state.new_milestone = 0
                        st.rerun()
                with cb:
                    if st.button("💪 继续完善更多细节",
                                 use_container_width=True, key="ms_lit_continue"):
                        st.session_state.new_milestone = 0
                        st.rerun()
        else:
            st.balloons()
            _product_complete_dialog(idea)
    else:
        st.balloons()
        with st.container(border=True):
            mc1, mc2 = st.columns([7, 3])
            with mc1:
                st.success(
                    f"🎉 **阶段 {milestone} 完成：{s_info['title']}！** "
                    f"已把{s_info['desc'].replace('·', '、')}想清楚了，继续加油！"
                )
            with mc2:
                if st.button("继续梳理下一阶段 →", type="primary",
                             use_container_width=True, key="ms_continue"):
                    st.session_state.new_milestone = 0
                    st.rerun()

# ─── Product mode chat ────────────────────────────────────────────────────────
def _chat_product(idea: dict):
    st.subheader("对话")
    done_count = len(get_completed_stages(idea))
    st.progress(done_count / 3, text=f"引导进度：{done_count} / 3 个阶段完成")

    if st.session_state.get("stage3_choice") == "prompt" and idea.get("ai_prompt"):
        st.info("✅ 开发规格文档已生成！点击右侧「📐 开发规格」Tab 查看和下载。")

    st.markdown("---")
    _render_chat_history(idea)
    _render_milestone_inline(idea, GUIDED_STAGES, is_lit=False)
    _render_retry_buttons(idea)

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

    st.markdown("---")
    _render_chat_history(idea)
    _render_milestone_inline(idea, LIT_STAGES, is_lit=True)
    _render_retry_buttons(idea)

    hide_input = st.session_state.get("new_milestone") == len(LIT_STAGES)
    if not st.session_state.processing and not hide_input:
        answer = st.chat_input("回答问题…（不确定说「跳过」，后续可以再补充修改）")
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

# ─── 重试 / 重新生成按钮（共用）──────────────────────────────────────────────
def _render_retry_buttons(idea: dict):
    """根据最后一条可见消息的角色，显示重试或重新生成按钮。"""
    if st.session_state.processing:
        return
    visible = [m for m in idea.get("messages", []) if not m.get("hidden")]
    if not visible:
        return
    last = visible[-1]
    if last["role"] == "user":
        # AI 未能成功响应，提供重试
        if st.button("🔄 重试", key="btn_retry", help="重新请求 AI 回答"):
            st.session_state.processing = True
            st.rerun()
    elif last["role"] == "assistant":
        # 允许重新生成最后一条回答
        if st.button("🔄 重新生成", key="btn_regen", help="删除最后一条回答，重新请求"):
            idea["messages"].remove(last)
            save_idea(idea)
            st.session_state.processing = True
            st.rerun()

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
    sys_msgs = [
        {"role": "system", "content": MAIN_PROMPT},
        {"role": "system", "content": get_stage_prompt(idea)},
    ]
    with st.chat_message("assistant"):
        thinking  = st.empty()
        full_text = ""
        thinking.markdown("💭 _AI正在思考..._")
        try:
            full_text = _call_with_retry(sys_msgs, msgs, thinking)
        except openai.RateLimitError as e:
            thinking.empty()
            st.error(f"⏳ 请求频率超限（429），分批重试后仍未恢复，请稍等片刻再试。\n\n> {e}")
            st.session_state.processing = False
            st.stop()
        except Exception as e:
            thinking.empty()
            st.error(f"调用失败：{e}")
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
    sys_prompt    = build_lit_system_prompt(idea.get("lit_type", ""), idea.get("lit_subtype", ""))
    sys_msgs = [
        {"role": "system", "content": sys_prompt},
        {"role": "system", "content": get_lit_stage_prompt(idea)},
    ]
    with st.chat_message("assistant"):
        thinking  = st.empty()
        full_text = ""
        thinking.markdown("💭 _AI正在思考..._")
        try:
            full_text = _call_with_retry(sys_msgs, msgs, thinking)
        except openai.RateLimitError as e:
            thinking.empty()
            st.error(f"⏳ 请求频率超限（429），分批重试后仍未恢复，请稍等片刻再试。\n\n> {e}")
            st.session_state.processing = False
            st.stop()
        except Exception as e:
            thinking.empty()
            st.error(f"调用失败：{e}")
            st.session_state.processing = False
            st.stop()
        thinking.empty()
        parsed  = extract_json(full_text)
        display = {}
        if parsed:
            if parsed.get("outline"):
                # Preserve character_relationships (managed manually, not by AI)
                cr = idea.get("outline", {}).get("character_relationships", [])
                idea["outline"] = parsed["outline"]
                if not idea["outline"].get("character_relationships"):
                    idea["outline"]["character_relationships"] = cr
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
