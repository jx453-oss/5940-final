# RAG + 联网搜索 + deptId 集成 功能更新文档

## 概述

本项目经历了多个重大版本更新：

1. **v1.0 - RAG 集成**：基于学校知识库的检索增强生成功能
2. **v2.0 - 联网搜索兜底**：当知识库相关性不足时自动启用联网搜索
3. **v2.1 - 前端界面升级**：全新设计的聊天界面，支持来源展示
4. **v3.0 - deptId 集成**：使用用户部门ID自动映射学校，移除 school_id 参数

---

## v3.0 重大变更：deptId 集成

### 为什么改用 deptId？

在实际 App 中，用户登录后系统已知用户所属学校（通过 `/app/user/info` 的 `deptId`）。App 只需透传 `deptId`，后端自动映射到对应学校知识库。

### 参数变更

| 变更项 | 旧版本 (v2.x) | 新版本 (v3.0) |
|--------|---------------|---------------|
| 学校标识参数 | `school_id` (如 "UCLA") | `deptId` (如 214) |
| 参数来源 | 前端手动传入 | 从用户信息接口获取 |
| 必填参数 | `question`, `school_id` | `question`, `deptId` |

### deptId 与学校映射表

| deptId | school_id | 学校名称 |
|--------|-----------|----------|
| 211 | UCB | 加州大学伯克利分校 |
| 213 | USC | 南加州大学 |
| 214 | UCLA | 加州大学洛杉矶分校 |
| 216 | UCSD | 加州大学圣地亚哥分校 |
| 218 | UW | 华盛顿大学 |
| 226 | NYU | 纽约大学 |

### 代码变更

#### config.py 新增映射

```python
# 学校配置中添加 deptId
SCHOOLS = {
    'UCLA': {'name': 'UC Los Angeles', 'name_cn': '加州大学洛杉矶分校', 'file': 'UCLACU', 'deptId': 214},
    # ...
}

# 新增反向映射
DEPT_TO_SCHOOL = {
    211: 'UCB',   # 加州大学伯克利分校
    213: 'USC',   # 南加州大学
    214: 'UCLA',  # 加州大学洛杉矶分校
    216: 'UCSD',  # 加州大学圣地亚哥分校
    218: 'UW',    # 华盛顿大学
    226: 'NYU',   # 纽约大学
}
```

#### app.py 参数处理

```python
# 获取 deptId（支持驼峰和下划线两种格式）
dept_id = data.get('deptId') or data.get('dept_id')

# 验证 deptId
if not dept_id:
    return jsonify({
        'error': 'deptId 不能为空',
        'available_dept_ids': list(Config.DEPT_TO_SCHOOL.keys())
    }), 400

# 通过 deptId 映射获取 school_id
school_id = Config.DEPT_TO_SCHOOL.get(dept_id)
if not school_id:
    return jsonify({
        'error': f'未找到部门ID对应的学校: {dept_id}',
        'available_dept_ids': list(Config.DEPT_TO_SCHOOL.keys())
    }), 400
```

---

## 与原版本的主要区别

### 原版本 (基础千问 API)
- 简单的问答接口，无知识库支持
- 无学校区分
- AI 无特定身份，通用回答
- 前端只有基础输入框

### 新版本 (RAG + 联网搜索 + deptId)
- 基于学校文档的知识库检索
- 通过 `deptId` 自动映射学校
- AI 具有学校专属身份
- 智能判断：知识库优先，联网搜索兜底
- 返回来源信息和相关度分数
- 全新前端界面，展示来源引用

---

## 文件变更清单

### 新增文件
| 文件 | 说明 |
|------|------|
| `rag_service.py` | RAG 服务模块（检索、system prompt 生成） |
| `build_knowledge_base.py` | 知识库构建脚本 |
| `vector_store/` | 向量知识库存储目录（9个学校子目录） |

### 修改文件
| 文件 | 修改内容 |
|------|---------|
| `config.py` | 添加学校配置（含 deptId）、DEPT_TO_SCHOOL 映射、RAG 配置、联网搜索配置 |
| `requirements.txt` | 添加 RAG 相关依赖 |
| `app.py` | 集成 RAG + 联网搜索，使用 deptId 参数，新增 `/schools` 接口 |
| `index.html` | 全新前端界面设计，使用 deptId 调用 API |

### 新增依赖
```
llama-index-core==0.10.67
llama-index-embeddings-dashscope==0.1.4
llama-index-readers-file==0.1.33
llama-index-postprocessor-dashscope-rerank-custom==0.1.0
docx2txt==0.8
pydantic>=2.7.0
```

---

## app.py 核心变化详解

### 1. 新增导入
```python
from rag_service import retrieve, get_system_prompt
```

### 2. 新增函数：`call_ai_with_web_search()`
```python
def call_ai_with_web_search(messages, enable_search=False, search_strategy='standard'):
    """
    调用千问API，支持联网搜索功能

    参数：
    - enable_search: 是否启用联网搜索
    - search_strategy: 搜索策略 ('standard' 或 'pro')

    返回：
    - tuple: (answer, sources) - 回答内容和来源信息
    """
```

### 3. `/ask` 接口重大变化

**原版本流程：**
```
用户问题 → 直接调用千问 API → 返回回答
```

**v2.x 版本流程：**
```
用户问题 + school_id → 验证 school_id → RAG 检索 → 调用千问 API
```

**v3.0 版本流程：**
```
用户问题 + deptId
    ↓
deptId → school_id 映射
    ↓
RAG 检索知识库内容
    ↓
评估检索质量 (rag_score)
    ↓
rag_score >= 0.5 → 使用知识库内容
rag_score < 0.5  → 启用联网搜索
    ↓
生成学校专属 System Prompt
    ↓
调用千问 API (可能带联网搜索)
    ↓
返回回答 + 来源类型 + 分数 + 来源链接
```

**请求参数变化：**
| 参数 | v1.0 | v2.x | v3.0 |
|------|------|------|------|
| question | 必填 | 必填 | 必填 |
| session_id | 可选 | 可选 | 可选 |
| school_id | 无 | **必填** | 移除 |
| deptId | 无 | 无 | **必填** |

**响应参数变化：**
| 参数 | v1.0 | v2.x/v3.0 |
|------|------|-----------|
| session_id | 有 | 有 |
| question | 有 | 有 |
| answer | 有 | 有 |
| school_id | 无 | **新增** (后端映射得出) |
| source_type | 无 | **新增** (knowledge_base / web_search) |
| rag_score | 无 | **新增** (0-1 相关度分数) |
| web_sources | 无 | **新增** (联网搜索来源) |

---

## API 接口文档

### POST /ask - 提问接口

**请求：**
```json
{
  "question": "UCLA的SIR截止日期是什么时候？",
  "deptId": 214,
  "session_id": "可选"
}
```

**响应（知识库回答）：**
```json
{
  "session_id": "uuid",
  "school_id": "UCLA",
  "question": "UCLA的SIR截止日期是什么时候？",
  "answer": "加州大学洛杉矶分校（UCLA）的SIR截止日期是2024年5月15日...",
  "source_type": "knowledge_base",
  "rag_score": 0.621
}
```

**响应（联网搜索回答）：**
```json
{
  "session_id": "uuid",
  "school_id": "UCLA",
  "question": "2024年美国总统大选结果是什么？",
  "answer": "2024年美国总统大选中，共和党候选人特朗普宣布获胜[1][2]...",
  "source_type": "web_search",
  "rag_score": 0.279,
  "web_sources": {
    "search_results": [
      {
        "index": 1,
        "title": "2024年美利坚合众国总统选举",
        "url": "https://baike.baidu.com/...",
        "site_name": "百度百科"
      },
      {
        "index": 2,
        "title": "2024年美国大选结果公布",
        "url": "https://kan.china.com/...",
        "site_name": "中华网"
      }
    ]
  }
}
```

### 响应字段说明

| 字段 | 说明 |
|------|------|
| session_id | 会话ID，用于多轮对话 |
| school_id | 学校ID（后端通过 deptId 映射得出）|
| source_type | 回答来源：`knowledge_base`（知识库）或 `web_search`（联网搜索）|
| rag_score | RAG 检索相关性分数（0-1），越高表示知识库匹配度越好 |
| web_sources | 联网搜索来源信息（仅当 source_type 为 web_search 时存在）|

### GET /schools - 获取学校列表

**响应：**
```json
{
  "schools": {
    "UCLA": {"name": "UC Los Angeles", "name_cn": "加州大学洛杉矶分校", "file": "UCLACU", "deptId": 214},
    "UCB": {"name": "UC Berkeley", "name_cn": "加州大学伯克利分校", "file": "UCBCU", "deptId": 211},
    ...
  }
}
```

---

## 联网搜索引用处理

当 `source_type` 为 `web_search` 时，回答中的 `[1][2]` 等标记对应 `web_sources.search_results` 中的来源。

**前端处理示例（index.html 中的实现）：**

```javascript
// 1. 将 [1] 转换为上标格式
let formattedAnswer = data.answer.replace(/\[(\d+)\]/g, '<sup>[$1]</sup>');

// 2. 展示来源卡片
if (data.web_sources && data.web_sources.search_results) {
    const sourcesHtml = data.web_sources.search_results.map(source => `
        <div class="source-card">
            <span class="source-index">[${source.index}]</span>
            <a href="${source.url}" target="_blank" class="source-title">${source.title}</a>
            <span class="source-site">${source.site_name}</span>
        </div>
    `).join('');

    sourcesContainer.innerHTML = `
        <div class="sources-header">参考来源</div>
        ${sourcesHtml}
    `;
}
```

---

## 技术实现详解

### RAG 检索流程
1. 通过 deptId 映射获取 school_id
2. 加载学校对应的向量索引（带缓存）
3. 使用 DashScope Embedding 进行向量检索
4. 获取 top-20 候选结果
5. 使用 DashScope Rerank 重排序，取 top-5
6. 根据相似度阈值筛选有效结果
7. 返回内容、最高分数、是否高质量

### 联网搜索兜底机制
当 `rag_score < 0.5` 时自动触发：
- 调用千问 API 时启用 `enable_search=True`
- 设置 `enable_source=True` 获取来源
- 设置 `enable_citation=True` 启用引用标记
- AI 回答中包含 `[1][2]` 等引用
- 返回 `web_sources` 字段包含来源详情

### System Prompt 设计
根据不同场景生成不同提示词：

**知识库模式：**
```
你是{学校中文名}（{学校英文名}）的专属AI助手。
请基于以下参考资料回答学生的问题：
{检索到的知识库内容}
...
```

**联网搜索模式：**
```
你是{学校中文名}（{学校英文名}）的专属AI助手。
当前问题在知识库中没有找到高度相关的信息，系统已启用联网搜索功能...
```

---

## 配置参数说明

在 `config.py` 中可调整：

```python
# 学校配置（含 deptId）
SCHOOLS = {
    'UCLA': {'name': 'UC Los Angeles', 'name_cn': '加州大学洛杉矶分校', 'file': 'UCLACU', 'deptId': 214},
    ...
}

# deptId 到 school_id 的反向映射
DEPT_TO_SCHOOL = {
    211: 'UCB',
    213: 'USC',
    214: 'UCLA',
    216: 'UCSD',
    218: 'UW',
    226: 'NYU',
}

# RAG 配置
SCHOOL_DATA_PATH = 'school_data'      # 源文件目录（可删除）
VECTOR_STORE_PATH = 'vector_store'    # 向量库目录（必须保留）
RAG_SIMILARITY_THRESHOLD = 0.2        # 最低相似度阈值
RAG_HIGH_QUALITY_THRESHOLD = 0.5      # 高质量阈值（低于此值触发联网搜索）
RAG_CHUNK_COUNT = 5                   # 检索片段数量

# 联网搜索配置
ENABLE_WEB_SEARCH_FALLBACK = True     # 是否启用联网搜索兜底
WEB_SEARCH_STRATEGY = 'standard'      # 搜索策略: standard 或 pro
```

---

## 前端界面更新

### 新增功能
- 学校选择下拉菜单（仅显示有 deptId 的学校）
- 使用 deptId 调用 API
- 现代化聊天气泡界面
- 来源类型徽章（知识库/联网搜索）
- RAG 相关度百分比显示
- 联网搜索来源卡片（可点击链接）
- 快速问题按钮
- 加载动画
- 响应式设计

### 来源展示效果
联网搜索回答会显示：
- 回答内容中的 `[1][2]` 转为上标格式
- 回答下方显示"参考来源"卡片
- 每个来源显示编号、标题（可点击）、网站名

---

## App 端集成指南

### 调用流程

```
1. 用户登录 App
       ↓
2. 调用 /app/user/info 获取用户信息
       ↓
3. 提取 deptId（如 214）
       ↓
4. 用户提问时，发送请求到 /ask：
   {
     "question": "用户的问题",
     "deptId": 214
   }
       ↓
5. 处理响应，展示回答
```

### 示例代码

```javascript
// 从用户信息获取 deptId
const userInfo = await getUserInfo();
const deptId = userInfo.deptId;  // 如 214

// 提问AI
const response = await fetch('http://your-server:8087/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: '住房申请截止日期是什么时候？',
        deptId: deptId
    })
});

const data = await response.json();

// 处理回答
if (data.source_type === 'web_search' && data.web_sources) {
    // 处理联网搜索引用
    let answer = data.answer.replace(/\[(\d+)\]/g, '<sup>[$1]</sup>');
    showSourceCards(data.web_sources.search_results);
}
```

---

## API 调用成本变化

| 项目 | 原版本 | 新版本 |
|------|--------|--------|
| 大模型调用 | qwen-plus | qwen-plus |
| Embedding | 无 | DashScope text-embedding-v2 |
| Rerank | 无 | DashScope rerank |
| 联网搜索 | 无 | 可选（按需触发） |

> 注意：每次问答会额外消耗 Embedding 和 Rerank 的 API 配额

---

## 部署说明

### 首次部署
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API 密钥
cp .env.example .env
# 编辑 .env 设置 DASHSCOPE_API_KEY

# 3. 确保 vector_store/ 目录存在

# 4. 启动服务
python app.py
```

### 更新知识库
```bash
# 将 docx 文件放入 school_data/
python build_knowledge_base.py UCI     # 构建单个学校
python build_knowledge_base.py all     # 构建所有学校
```

### 交付文件清单
必须包含：
- `app.py`
- `config.py`
- `rag_service.py`
- `requirements.txt`
- `vector_store/` 目录及所有子目录
- `index.html`
- `.env.example`

可选删除：
- `school_data/` (已向量化，建议备份)
- `build_knowledge_base.py` (仅构建时需要)
- `test_*.py` (测试文件)

---

## 错误处理

| 错误场景 | 响应 |
|---------|------|
| 缺少 `deptId` | 400 + 可用 deptId 列表 |
| 无效的 `deptId` | 400 + 可用 deptId 列表 |
| 知识库不存在 | 使用联网搜索或通用回答 |
| API 调用失败 | 500 + 错误信息 |
