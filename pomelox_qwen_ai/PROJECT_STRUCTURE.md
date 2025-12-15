# 项目结构说明

```
pomelox_qwen_ai/
│
├── app.py                    # 主应用文件，包含所有API接口（含联网搜索）
├── config.py                 # 配置文件（含学校、deptId映射、RAG、联网搜索配置）
├── rag_service.py            # RAG服务模块
├── build_knowledge_base.py   # 知识库构建脚本
├── requirements.txt          # 项目依赖列表
│
├── test_api.py               # 基础API测试脚本
├── test_ask_api.py           # Ask接口测试脚本
├── test_rag_api.py           # RAG功能测试脚本
├── test_results.json         # 测试结果示例
│
├── README.md                 # 项目说明文档（中文）
├── README.en.md              # 项目说明文档（英文）
├── API_DOCUMENTATION.md      # API接口文档
├── PROJECT_STRUCTURE.md      # 项目结构说明
├── RAG_UPDATE.md             # RAG + 联网搜索 + deptId 更新说明
│
├── .env                      # 环境变量配置文件
├── .env.example              # 环境变量配置文件示例
├── index.html                # 前端演示页面（现代化UI）
│
├── vector_store/             # 向量知识库存储目录
│   ├── UCI/                  # UCI学校向量库
│   ├── UCSD/                 # UCSD学校向量库（deptId: 216）
│   ├── NYU/                  # NYU学校向量库（deptId: 226）
│   ├── OSU/                  # OSU学校向量库
│   ├── UCB/                  # UCB学校向量库（deptId: 211）
│   ├── UCLA/                 # UCLA学校向量库（deptId: 214）
│   ├── UPenn/                # UPenn学校向量库
│   ├── USC/                  # USC学校向量库（deptId: 213）
│   └── UW/                   # UW学校向量库（deptId: 218）
│
└── venv/                     # Python虚拟环境
```

## 文件详细说明

### 核心文件

#### app.py
主应用文件，实现了五个核心接口：
1. `/ask` - POST接口，用于向AI提问（RAG + 联网搜索，使用 deptId 参数）
2. `/schools` - GET接口，获取可用学校列表（含 deptId 信息）
3. `/history/<session_id>` - GET接口，查询对话历史
4. `/clear/<session_id>` - DELETE接口，清除会话记录
5. `/health` - GET接口，健康检查

**关键函数：**
- `call_ai_with_web_search(messages, enable_search, search_strategy)`: 调用千问API，支持联网搜索
- `ask_ai()`: 核心问答逻辑，集成 deptId 映射、RAG 检索和联网搜索兜底

**deptId 参数处理：**
```python
# 获取 deptId（支持驼峰和下划线两种格式）
dept_id = data.get('deptId') or data.get('dept_id')

# 通过 deptId 映射获取 school_id
school_id = Config.DEPT_TO_SCHOOL.get(dept_id)
```

**联网搜索参数：**
```python
call_params['enable_search'] = True
call_params['search_options'] = {
    'search_strategy': 'standard',  # 或 'pro'
    'enable_source': True,          # 返回来源信息
    'enable_citation': True         # 启用引用标记 [1][2]
}
```

#### config.py
配置文件，包含：
- Flask密钥配置
- 千问API密钥配置
- 服务器配置（端口8087）
- 学校配置（9所美国大学，含 deptId）
- **deptId 到 school_id 的反向映射**
- RAG配置参数
- 联网搜索配置

```python
# 学校配置（含 deptId）
SCHOOLS = {
    'UCLA': {'name': 'UC Los Angeles', 'name_cn': '加州大学洛杉矶分校', 'file': 'UCLACU', 'deptId': 214},
    # ...
}

# deptId 到 school_id 的反向映射
DEPT_TO_SCHOOL = {
    211: 'UCB',   # 加州大学伯克利分校
    213: 'USC',   # 南加州大学
    214: 'UCLA',  # 加州大学洛杉矶分校
    216: 'UCSD',  # 加州大学圣地亚哥分校
    218: 'UW',    # 华盛顿大学
    226: 'NYU',   # 纽约大学
}

# RAG 配置
RAG_SIMILARITY_THRESHOLD = 0.2        # 最低相似度阈值
RAG_HIGH_QUALITY_THRESHOLD = 0.5      # 高质量阈值（低于此值触发联网搜索）
RAG_CHUNK_COUNT = 5                   # 检索片段数量

# 联网搜索配置
ENABLE_WEB_SEARCH_FALLBACK = True     # 是否启用联网搜索兜底
WEB_SEARCH_STRATEGY = 'standard'      # 搜索策略: standard 或 pro
```

#### rag_service.py
RAG服务模块，提供：
- `load_index(school_id)`: 加载学校向量索引（带缓存）
- `retrieve(school_id, query)`: 检索相关文档片段，返回 `(content, max_score, has_high_quality)`
- `get_system_prompt(school_id, content, use_web_search)`: 生成学校特定的System Prompt

**返回值说明：**
- `content`: 检索到的知识库内容
- `max_score`: 最高相似度分数（0-1）
- `has_high_quality`: 是否为高质量匹配（score >= 0.5）

#### build_knowledge_base.py
知识库构建脚本，用于：
- 读取school_data/下的docx文件
- 为每个学校创建向量索引
- 保存到vector_store/目录

使用方法：
```bash
python build_knowledge_base.py list    # 列出可用文件
python build_knowledge_base.py all     # 构建所有学校知识库
python build_knowledge_base.py UCI     # 构建单个学校知识库
```

### 依赖文件

#### requirements.txt
项目依赖列表：
- dashscope: 阿里云千问API的Python SDK
- flask: Python Web框架
- flask-cors: 处理跨域请求
- python-dotenv: 环境变量管理
- llama-index-core: RAG核心框架
- llama-index-embeddings-dashscope: DashScope向量嵌入
- llama-index-readers-file: 文件读取器
- llama-index-postprocessor-dashscope-rerank-custom: 重排序后处理器
- docx2txt: Word文档解析
- pydantic: 数据验证

### 测试文件

#### test_api.py
基础API测试脚本，验证基本接口功能。

#### test_ask_api.py
Ask接口测试脚本，测试提问功能。

#### test_rag_api.py
RAG功能测试脚本，包含：
- 健康检查测试
- 学校列表测试
- 参数验证测试（缺少deptId、无效deptId）
- RAG问答测试
- 联网搜索测试
- 多轮对话测试
- 历史记录测试
- 会话清除测试

#### test_results.json
测试结果示例文件，包含知识库回答和联网搜索回答的完整JSON响应。

### 文档文件

#### README.md / README.en.md
项目说明文档，包含：
- 项目介绍
- **v3.0 变更说明（deptId 集成）**
- deptId 与学校映射表
- 智能回答机制说明
- 安装配置说明
- 接口文档
- App 端集成指南
- 联网搜索引用处理说明

#### API_DOCUMENTATION.md
详细的API接口文档，包含：
- v3.0 接口变更说明
- 所有接口的请求/响应格式（使用 deptId）
- 知识库回答和联网搜索回答示例
- 响应字段说明
- 联网搜索引用处理
- 错误响应说明
- App 端集成指南
- 多语言使用示例（JavaScript、cURL、Python）

#### RAG_UPDATE.md
RAG + 联网搜索 + deptId 功能更新说明，包含：
- 功能概述（v1.0 RAG → v2.0 联网搜索 → v2.1 前端升级 → v3.0 deptId 集成）
- **v3.0 重大变更说明**
- 与原版本的主要区别
- 文件变更清单
- app.py 核心变化详解
- API接口变更
- 技术实现详解
- 配置参数说明
- 部署说明

### 数据目录

#### vector_store/
向量知识库存储目录，包含9个学校的向量化数据。每个子目录包含LlamaIndex的持久化索引文件。

**deptId 映射的学校：**
- UCB (deptId: 211) - 加州大学伯克利分校
- USC (deptId: 213) - 南加州大学
- UCLA (deptId: 214) - 加州大学洛杉矶分校
- UCSD (deptId: 216) - 加州大学圣地亚哥分校
- UW (deptId: 218) - 华盛顿大学
- NYU (deptId: 226) - 纽约大学

**无 deptId 的学校（暂不支持 App 端调用）：**
- UCI - 加州大学尔湾分校
- OSU - 俄亥俄州立大学
- UPenn - 宾夕法尼亚大学

> 注意：此目录是运行服务必需的，请勿删除。

### 配置文件

#### .env
环境变量配置文件，包含实际的API密钥等敏感信息。

#### .env.example
环境变量配置文件示例，用于参考。

### 前端文件

#### index.html
现代化前端演示页面，功能包括：
- 学校选择下拉菜单（**仅显示有 deptId 的学校**）
- **使用 deptId 调用 API**
- 聊天气泡界面
- 来源类型徽章（📚 知识库 / 🌐 联网搜索）
- RAG 相关度百分比显示
- 联网搜索来源卡片（可点击链接）
- 快速问题按钮
- 加载动画
- 响应式设计

**前端 deptId 处理：**
```javascript
// 只显示有 deptId 的学校
for (const [id, info] of Object.entries(data.schools)) {
    if (info.deptId) {
        const option = document.createElement('option');
        option.value = info.deptId;  // 使用 deptId 作为 value
        option.dataset.schoolId = id;
        option.textContent = `${info.name_cn} (${id})`;
        select.appendChild(option);
    }
}

// 发送请求时使用 deptId
body: JSON.stringify({
    question: question,
    deptId: currentDeptId,  // 使用 deptId
    session_id: currentSessionId || undefined
})
```

---

## API 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话ID |
| school_id | string | 学校ID（后端通过 deptId 映射得出）|
| question | string | 用户提问 |
| answer | string | AI回答 |
| source_type | string | 来源类型：`knowledge_base` 或 `web_search` |
| rag_score | float | RAG检索相关性分数（0-1）|
| web_sources | object | 联网搜索来源（仅 web_search 时存在）|

## 智能切换逻辑

```
deptId → school_id 映射
       ↓
   RAG 检索知识库
       ↓
rag_score >= 0.5 → 使用知识库 (source_type: knowledge_base)
rag_score < 0.5  → 联网搜索 (source_type: web_search)
```

## 联网搜索引用处理

当 `source_type` 为 `web_search` 时，回答中会包含 `[1][2]` 等引用标记，对应 `web_sources.search_results` 中的来源。

**处理示例：**
```javascript
// 将 [1] 转换为上标格式
let formattedAnswer = data.answer.replace(/\[(\d+)\]/g, '<sup>[$1]</sup>');

// 展示来源卡片
if (data.web_sources && data.web_sources.search_results) {
    data.web_sources.search_results.forEach(source => {
        // source.index: 编号
        // source.title: 标题
        // source.url: 链接（可点击）
        // source.site_name: 网站名称
    });
}
```
