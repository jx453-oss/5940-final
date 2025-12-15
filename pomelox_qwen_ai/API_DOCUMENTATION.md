# API 接口文档

## 概述

本服务提供基于 RAG（检索增强生成）的学校专属 AI 问答接口，支持：
- 基于学校知识库的智能问答
- 知识库不足时自动联网搜索
- 多轮对话会话管理
- 通过用户 deptId 自动匹配学校

**服务地址：** `http://localhost:8087`

---

## 重要变更说明（v3.0）

### 接口参数变更

| 变更项 | 旧版本 | 新版本 |
|--------|--------|--------|
| 学校标识参数 | `school_id` (如 "UCLA") | `deptId` (如 214) |
| 参数来源 | 前端手动传入 | 从用户信息接口获取 |

### 为什么改用 deptId？

在实际 App 中，用户登录后系统已经知道用户属于哪个学校（通过 `/app/user/info` 接口的 `deptId` 字段）。因此：
- App 端只需透传用户的 `deptId`
- 后端自动映射到对应的学校知识库
- 用户无需手动选择学校

### deptId 与学校映射表

| deptId | school_id | 学校名称 |
|--------|-----------|---------|
| 211 | UCB | 加州大学伯克利分校 |
| 213 | USC | 南加州大学 |
| 214 | UCLA | 加州大学洛杉矶分校 |
| 216 | UCSD | 加州大学圣地亚哥分校 |
| 218 | UW | 华盛顿大学 |
| 226 | NYU | 纽约大学 |

---

## 1. 提问AI接口（核心接口）

### 基本信息
- **URL**: `/ask`
- **方法**: POST
- **描述**: 向AI提问并获取基于学校知识库或联网搜索的回答

### 请求参数 (JSON格式)
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| question | string | 是 | 用户提出的问题 |
| deptId | integer | 是 | 用户部门ID（从用户信息接口获取） |
| session_id | string | 否 | 会话ID，如果不提供则自动生成 |

> **注意**：`deptId` 也支持 `dept_id` 格式（下划线命名）

### 请求示例
```json
{
  "question": "UCLA的SIR截止日期是什么时候？",
  "deptId": 214,
  "session_id": "3944f3a7-e07d-46fd-a6de-811aa738315fa"
}
```

### 响应参数
| 参数名 | 类型 | 说明 |
|--------|------|------|
| session_id | string | 会话ID |
| school_id | string | 学校ID（由 deptId 映射得到） |
| question | string | 用户提出的问题 |
| answer | string | AI的回答 |
| source_type | string | 回答来源：`knowledge_base`（知识库）或 `web_search`（联网搜索） |
| rag_score | float | RAG检索相关性分数（0-1），越高表示知识库匹配度越好 |
| web_sources | object | 联网搜索来源信息（仅当 source_type 为 web_search 时存在） |

### 响应字段详解

#### source_type（来源类型）
| 值 | 说明 | 触发条件 |
|----|------|---------|
| `knowledge_base` | 回答基于学校知识库 | rag_score >= 0.5 |
| `web_search` | 回答基于联网搜索 | rag_score < 0.5 |

#### rag_score（相关性分数）
- 范围：0 到 1
- 含义：问题与知识库的匹配程度
- 用途：
  - **App 端可用于展示**：如显示"相关度: 62%"
  - **判断回答来源**：分数越高越可能来自知识库

#### web_sources（联网搜索来源）
仅当 `source_type` 为 `web_search` 时存在。

```json
{
  "search_results": [
    {
      "index": 1,
      "title": "网页标题",
      "url": "https://example.com/page",
      "site_name": "网站名称",
      "icon": "https://example.com/icon.png"
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| index | 引用编号，对应回答中的 [1][2] 等标记 |
| title | 网页标题 |
| url | 网页链接（可点击跳转） |
| site_name | 网站名称 |
| icon | 网站图标URL（可选） |

### 响应示例（知识库回答）
当问题在知识库中找到高相关内容时（rag_score >= 0.5）：
```json
{
  "session_id": "3944f3a7-e07d-46fd-a6de-811aa738315fa",
  "school_id": "UCLA",
  "question": "UCLA的SIR截止日期是什么时候？",
  "answer": "加州大学洛杉矶分校（UCLA）的注册意向声明（SIR）截止日期是2024年5月15日。您需要在此日期前登录已录取学生门户网站提交SIR，以正式接受录取通知...",
  "source_type": "knowledge_base",
  "rag_score": 0.621
}
```

### 响应示例（联网搜索回答）
当问题在知识库中相关性不足时（rag_score < 0.5），自动启用联网搜索：
```json
{
  "session_id": "05057fbe-7821-42d8-88df-84ebb10bbeb7",
  "school_id": "UCLA",
  "question": "2024年美国总统大选结果是什么？",
  "answer": "2024年美国总统大选中，共和党总统候选人唐纳德·特朗普宣布获胜[1][2]。民主党候选人卡玛拉·哈里斯已承认败选[1]...",
  "source_type": "web_search",
  "rag_score": 0.279,
  "web_sources": {
    "search_results": [
      {
        "index": 1,
        "title": "2024年美利坚合众国总统选举",
        "url": "https://baike.baidu.com/item/2024年美利坚合众国总统选举/66226719",
        "site_name": "百度百科",
        "icon": "https://mbs1.bdstatic.com/searchbox/mappconsole/image/20200630/db4d874a-872b-4b27-931d-775a91ed0003.png"
      },
      {
        "index": 2,
        "title": "尘埃落定!2024年美国大选结果公布",
        "url": "https://kan.china.com/article/5599508.html",
        "site_name": "中华网",
        "icon": "https://kan.china.com/apple-touch-icon-precomposed.png"
      }
    ]
  }
}
```

### 错误响应
| 状态码 | 错误信息 | 说明 |
|--------|----------|------|
| 400 | `{"error": "deptId 不能为空", "available_dept_ids": [...]}` | 未提供 deptId 参数 |
| 400 | `{"error": "无效的部门ID格式: XXX", "available_dept_ids": [...]}` | deptId 不是有效整数 |
| 400 | `{"error": "未找到部门ID对应的学校: XXX", "available_dept_ids": [...]}` | deptId 不在支持列表中 |
| 400 | `{"error": "问题不能为空且必须是字符串"}` | 问题参数为空或不是字符串 |
| 400 | `{"error": "请求体不能为空"}` | 请求体为空 |
| 400 | `{"error": "请求必须是JSON格式"}` | Content-Type不是application/json |
| 500 | `{"error": "服务器错误: ..."}` | 服务器内部错误 |

---

## 2. 获取学校列表接口

### 基本信息
- **URL**: `/schools`
- **方法**: GET
- **描述**: 获取所有支持的学校列表（含 deptId 映射信息）

### 请求示例
```
GET http://localhost:8087/schools
```

### 响应示例
```json
{
  "schools": {
    "UCI": {"name": "UC Irvine", "name_cn": "加州大学尔湾分校", "file": "UCI", "deptId": null},
    "UCSD": {"name": "UC San Diego", "name_cn": "加州大学圣地亚哥分校", "file": "UCSD", "deptId": 216},
    "NYU": {"name": "New York University", "name_cn": "纽约大学", "file": "NYUCU", "deptId": 226},
    "OSU": {"name": "Ohio State University", "name_cn": "俄亥俄州立大学", "file": "OSUCU", "deptId": null},
    "UCB": {"name": "UC Berkeley", "name_cn": "加州大学伯克利分校", "file": "UCBCU", "deptId": 211},
    "UCLA": {"name": "UC Los Angeles", "name_cn": "加州大学洛杉矶分校", "file": "UCLACU", "deptId": 214},
    "UPenn": {"name": "University of Pennsylvania", "name_cn": "宾夕法尼亚大学", "file": "UPennCU", "deptId": null},
    "USC": {"name": "University of Southern California", "name_cn": "南加州大学", "file": "USCCU", "deptId": 213},
    "UW": {"name": "University of Washington", "name_cn": "华盛顿大学", "file": "UWCU", "deptId": 218}
  }
}
```

> **说明**：`deptId` 为 `null` 的学校表示尚未与后端用户系统对接

---

## 3. 查询对话历史接口

### 基本信息
- **URL**: `/history/<session_id>`
- **方法**: GET
- **描述**: 查询指定会话的对话历史记录

### 请求示例
```
GET http://localhost:8087/history/3944f3a7-e07d-46fd-a6de-811aa738315fa
```

### 响应示例
```json
{
  "session_id": "3944f3a7-e07d-46fd-a6de-811aa738315fa",
  "school_id": "UCLA",
  "history": [
    {"role": "user", "content": "UCLA的SIR截止日期是什么时候？"},
    {"role": "assistant", "content": "加州大学洛杉矶分校（UCLA）的注册意向声明（SIR）截止日期是2024年5月15日..."}
  ]
}
```

---

## 4. 清除会话记录接口

### 基本信息
- **URL**: `/clear/<session_id>`
- **方法**: DELETE
- **描述**: 清除指定会话的所有记录

### 请求示例
```
DELETE http://localhost:8087/clear/3944f3a7-e07d-46fd-a6de-811aa738315fa
```

### 响应示例
```json
{
  "message": "会话记录已清除"
}
```

---

## 5. 健康检查接口

### 基本信息
- **URL**: `/health`
- **方法**: GET
- **描述**: 检查服务是否正常运行

### 响应示例
```json
{
  "status": "healthy"
}
```

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

### 响应处理建议

#### 1. 基础展示
```javascript
// 直接展示 AI 回答
displayMessage(data.answer);

// 可选：显示来源类型和相关度
if (data.source_type === 'knowledge_base') {
    showBadge('📚 知识库', `相关度: ${Math.round(data.rag_score * 100)}%`);
} else {
    showBadge('🌐 联网搜索', `相关度: ${Math.round(data.rag_score * 100)}%`);
}
```

#### 2. 处理联网搜索引用

AI 回答中可能包含 `[1][2]` 等引用标记，对应 `web_sources.search_results` 中的来源。

**处理方式 1：转换为上标格式**
```javascript
// 将 [1] 转换为上标 <sup>[1]</sup>
let formattedAnswer = data.answer.replace(/\[(\d+)\]/g, '<sup>[$1]</sup>');
```

**处理方式 2：展示来源列表**
```javascript
if (data.web_sources && data.web_sources.search_results) {
    data.web_sources.search_results.forEach(source => {
        // source.index: 编号（对应回答中的 [1][2]）
        // source.title: 标题
        // source.url: 链接（可点击跳转）
        // source.site_name: 网站名称
        // source.icon: 网站图标

        displaySourceCard(source);
    });
}
```

### 完整示例代码

#### JavaScript (Fetch API)
```javascript
// 从用户信息获取 deptId（假设已登录）
const userInfo = await getUserInfo();
const deptId = userInfo.deptId;  // 如 214

// 提问AI
async function askAI(question) {
    const response = await fetch('http://your-server:8087/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question: question,
            deptId: deptId,
            session_id: currentSessionId || undefined
        })
    });

    const data = await response.json();

    if (data.error) {
        showError(data.error);
        return;
    }

    // 保存 session_id 用于多轮对话
    currentSessionId = data.session_id;

    // 处理回答
    let answer = data.answer;

    // 如果是联网搜索，处理引用
    if (data.source_type === 'web_search' && data.web_sources) {
        // 将 [1][2] 转为上标
        answer = answer.replace(/\[(\d+)\]/g, '<sup>[$1]</sup>');

        // 展示来源卡片
        showSourceCards(data.web_sources.search_results);
    }

    // 展示回答
    displayAnswer(answer);

    // 展示元信息
    showMetaInfo({
        sourceType: data.source_type,
        ragScore: data.rag_score,
        schoolId: data.school_id
    });
}
```

#### cURL
```bash
# 使用 deptId 提问（UCLA 学生）
curl -X POST http://localhost:8087/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "UCLA的住房申请截止日期是什么时候？", "deptId": 214}'

# 使用 deptId 提问（可能触发联网搜索）
curl -X POST http://localhost:8087/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "今天的天气怎么样？", "deptId": 214}'
```

#### Python (requests)
```python
import requests

# 从用户信息获取 deptId
user_info = get_user_info()
dept_id = user_info['deptId']  # 如 214

# 提问AI
response = requests.post('http://localhost:8087/ask', json={
    'question': 'UCLA的SIR截止日期是什么时候？',
    'deptId': dept_id
})
data = response.json()

print(f"学校: {data['school_id']}")
print(f"来源类型: {data['source_type']}")
print(f"相关度分数: {data['rag_score']}")
print(f"回答: {data['answer']}")

# 如果是联网搜索，打印来源
if 'web_sources' in data:
    print("\n参考来源:")
    for source in data['web_sources']['search_results']:
        print(f"[{source['index']}] {source['title']}")
        print(f"    {source['url']}")
        print(f"    来源: {source['site_name']}")
```

---

## 注意事项

1. **deptId 必填**：所有问答请求必须提供有效的 deptId
2. **来源类型判断**：根据 `source_type` 字段判断回答来源
3. **联网搜索引用**：当 `source_type` 为 `web_search` 时，回答中的 `[1][2]` 等标记对应 `web_sources.search_results` 中的来源
4. **rag_score 含义**：分数越高表示问题与知识库匹配度越好，低于 0.5 会触发联网搜索
5. **会话管理**：使用相同的 `session_id` 可以保持多轮对话上下文
