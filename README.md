# 💡 Idea 需求分析器

一个基于 AI 的产品需求分析工具，帮助你把模糊的想法快速整理成结构化的 PRD 文档。

## ✨ 功能特性

- **三阶段引导**：引导你依次说清楚"是什么 → 给谁用 → 怎么做"，阶段完成有烟花庆祝 🎉
- **13 模块 PRD**：自动生成符合规范的产品需求文档
- **流程图可视化**：实时渲染 Mermaid 流程图，支持手动编辑
- **竞品分析**：支持联网实时搜索（火山引擎 Ark 平台），或基于训练数据分析
- **AI 开发 Prompt**：一键生成可直接甩给 AI 的完整开发提示词
- **测试用例生成**：自动生成功能测试用例
- **数据存储在浏览器 Session**，不写服务器文件，保护隐私

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`

### 3. 配置 API Key

打开后在**左侧边栏**填写：

| 字段 | 说明 |
|------|------|
| **API 请求地址** | 你的 API Endpoint，默认为火山引擎 Ark 地址 |
| **API Key** | 平台颁发的 Key，如 `sk-xxx` |
| **模型名称** | 模型 ID，如 `doubao-seed-2-0-pro-260215`、`gpt-4o` |
| **启用联网搜索** | 仅火山引擎 Ark 平台支持，需在控制台开通「联网内容插件」 |

## 🔑 支持的 API 平台

本工具支持任何兼容 OpenAI Chat Completions 格式的平台，例如：

| 平台 | API 地址 | 说明 |
|------|----------|------|
| **火山引擎 Ark**（推荐）| `https://ark.cn-beijing.volces.com/api/v3` | 支持联网搜索，默认配置 |
| **OpenAI** | `https://api.openai.com/v1` | 使用 `gpt-4o` 等模型 |
| **智谱 AI** | `https://open.bigmodel.cn/api/paas/v4` | 使用 `glm-4` 等模型 |
| **月之暗面** | `https://api.moonshot.cn/v1` | 使用 `moonshot-v1-8k` 等 |
| **DeepSeek** | `https://api.deepseek.com/v1` | 使用 `deepseek-chat` |

## 📁 项目结构

```
.
├── app.py           # 主程序
├── requirements.txt # 依赖列表
└── README.md        # 说明文档
```

## 🛠️ 技术栈

- [Streamlit](https://streamlit.io/) - Web 界面
- [OpenAI Python SDK](https://github.com/openai/openai-python) - API 调用
- [Mermaid.js](https://mermaid.js.org/) - 流程图渲染
- [httpx](https://www.python-httpx.org/) - HTTP 客户端（联网搜索）

## 📝 注意事项

- 数据存储在浏览器 Session State，**刷新页面数据会清空**，使用前请导出保存
- 联网搜索功能仅火山引擎 Ark 平台支持，需在控制台额外开通
- API Key 仅在当前浏览器 Session 中使用，不会上传到任何服务器

## 📄 License

MIT License
