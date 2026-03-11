# 💡 Idea 需求分析器

一个基于 AI 的双模式创意分析工具：帮你把模糊的想法快速整理成结构化的 PRD 文档，或梳理成完整的文学创作蓝图。

## ✨ 功能特性

### 📦 产品需求模式
- **三阶段引导**：依次引导"是什么 → 给谁用 → 怎么做"，阶段完成有烟花庆祝 🎉
- **13 模块 PRD**：自动生成符合规范的产品需求文档
- **流程图可视化**：实时渲染 Mermaid 流程图，支持手动编辑
- **竞品分析**：支持联网实时搜索（火山引擎 Ark 平台）或基于训练数据分析
- **开发规格文档**：一键生成 ASCII 线框图 + 业务泳道图 + 功能规格，直接喂给 AI
- **测试用例生成**：自动生成功能测试用例
- **版本历史**：生成开发规格前可存版本快照，支持查看和回退历史版本
- **多格式导出**：PRD 可导出为 Markdown / HTML（可打印为 PDF）/ Confluence Wiki / Notion

### ✍️ 文学创作模式
- **细分类型选择**：新建时选择 📚 小说 / 🎭 剧本 / 🌿 散文 / 🎵 诗歌，小说还可细分言情/群像/悬疑/剧情/混合，AI 针对性引导
- **五阶段引导**：背景设定 → 人物塑造 → 冲突结构 → 写作计划 → 参考资料
- **👤 人物档案 Tab**：卡片式展示，支持增删改每个人物（姓名/角色定位/性格特征/人物弧光）
- **🕸️ 关系网 Tab**：vis.js 可视化人物关系图谱 + 关系表格增删改
- **故事大纲**：logline / 类型风格 / 世界观 / 冲突结构 / 人物关系全覆盖
- **多格式导出**：创作蓝图可导出为 Markdown / HTML（可打印为 PDF）/ Confluence Wiki / Notion

### 💾 数据持久化
- **自动本地保存**：每次操作自动写入 `ideas_data.json`，重启应用数据完整恢复
- **导出备份**：一键导出全部数据为 JSON 文件，可跨设备迁移
- **导入恢复**：上传备份文件即可合并恢复所有创意

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
├── app.py            # 主程序
├── ideas_data.json   # 本地数据文件（自动生成，勿手动删除）
├── requirements.txt  # 依赖列表
└── README.md         # 说明文档
```

## 🛠️ 技术栈

- [Streamlit](https://streamlit.io/) - Web 界面
- [OpenAI Python SDK](https://github.com/openai/openai-python) - API 调用
- [Mermaid.js](https://mermaid.js.org/) - 流程图渲染
- [vis-network](https://visjs.github.io/vis-network/) - 人物关系图谱
- [httpx](https://www.python-httpx.org/) - HTTP 客户端（联网搜索）

## 📝 注意事项

- 数据自动保存到本地 `ideas_data.json`，重启后自动恢复，无需手动导出
- 建议定期使用侧边栏「导出全部数据」备份，以防文件意外损坏
- 联网搜索功能仅火山引擎 Ark 平台支持，需在控制台额外开通
- API Key 仅在当前浏览器 Session 中使用，不会上传到任何服务器

## 📄 License

MIT License
