# Qwen API Python Project (RAG + Web Search + deptId Integration)

## Project Overview

A Flask-based web service that integrates with Alibaba Cloud's Qwen API, featuring:

- **RAG (Retrieval-Augmented Generation)**: School-specific intelligent Q&A based on knowledge base
- **Web Search Fallback**: Automatic web search when knowledge base relevance is low
- **deptId Auto-Mapping**: Automatically match school by user's department ID
- **Multi-turn Conversation**: Session management with context memory

### Core Features
1. AI Q&A endpoint (RAG priority + Web Search fallback)
2. Query conversation history
3. Clear session records
4. Get school list
5. Health check endpoint

---

## Important: API Parameter Changes

### v3.0 Changes

| Change Item | Old Version | New Version |
|-------------|-------------|-------------|
| School identifier | `school_id` (e.g., "UCLA") | `deptId` (e.g., 214) |
| Parameter source | Frontend manually passed | From user info API |

### Why Switch to deptId?

In the actual App, after user login, the system knows which school the user belongs to (via `/app/user/info` endpoint's `deptId`). The App only needs to pass through the `deptId`, and the backend automatically maps it to the corresponding school knowledge base.

### deptId to School Mapping

| deptId | school_id | School Name |
|--------|-----------|-------------|
| 211 | UCB | University of California, Berkeley |
| 213 | USC | University of Southern California |
| 214 | UCLA | University of California, Los Angeles |
| 216 | UCSD | University of California, San Diego |
| 218 | UW | University of Washington |
| 226 | NYU | New York University |

---

## Intelligent Response Mechanism

```
User Question + deptId
       ↓
   deptId → school_id Mapping
       ↓
   RAG Knowledge Base Retrieval
       ↓
  Evaluate Retrieval Quality (rag_score)
       ↓
┌──────────────────────────────────┐
│  rag_score >= 0.5                │
│  → Use knowledge base content    │
│  → source_type: knowledge_base   │
├──────────────────────────────────┤
│  rag_score < 0.5                 │
│  → Enable web search             │
│  → source_type: web_search       │
│  → Return citation links         │
└──────────────────────────────────┘
```

---

## Installation

```bash
# Activate virtual environment (if using)
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

If you encounter network issues, use Aliyun mirror:
```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## Configuration

1. Get Qwen API Key:
   - Visit Alibaba Cloud Console
   - Go to DashScope management page
   - Create and obtain API Key

2. Set API Key:
   - Copy `.env.example` to `.env`
   - Fill in your actual API key in `.env`

## Start Service

```bash
python app.py
```

Service runs at `http://localhost:8087` by default.

---

## API Endpoints

### 1. Ask AI Endpoint (Core)

- **URL**: `/ask`
- **Method**: POST
- **Request**:
  ```json
  {
    "question": "What is UCLA's SIR deadline?",
    "deptId": 214,
    "session_id": "optional session ID"
  }
  ```

- **Response (Knowledge Base)**:
  ```json
  {
    "session_id": "session ID",
    "school_id": "UCLA",
    "question": "What is UCLA's SIR deadline?",
    "answer": "UCLA's SIR deadline is May 15, 2024...",
    "source_type": "knowledge_base",
    "rag_score": 0.621
  }
  ```

- **Response (Web Search)**:
  ```json
  {
    "session_id": "session ID",
    "school_id": "UCLA",
    "question": "What is the 2024 US presidential election result?",
    "answer": "In the 2024 US presidential election, Donald Trump won[1][2]...",
    "source_type": "web_search",
    "rag_score": 0.279,
    "web_sources": {
      "search_results": [
        {
          "index": 1,
          "title": "2024 US Presidential Election",
          "url": "https://...",
          "site_name": "News Site"
        }
      ]
    }
  }
  ```

### Response Field Description

| Field | Description |
|-------|-------------|
| source_type | Answer source: `knowledge_base` or `web_search` |
| rag_score | RAG retrieval relevance score (0-1), higher means better match |
| web_sources | Web search source info (only exists when source_type is web_search) |

### Web Search Citation Handling

When `source_type` is `web_search`, markers like `[1][2]` in the answer correspond to sources in `web_sources.search_results`.

**Frontend handling example**:
```javascript
// Convert [1] to superscript format
let formattedAnswer = data.answer.replace(/\[(\d+)\]/g, '<sup>[$1]</sup>');

// Display source cards
if (data.web_sources) {
    data.web_sources.search_results.forEach(source => {
        // source.index: number
        // source.title: title
        // source.url: link (clickable)
        // source.site_name: website name
    });
}
```

### 2. Get School List

- **URL**: `/schools`
- **Method**: GET
- **Response**:
  ```json
  {
    "schools": {
      "UCLA": {"name": "UC Los Angeles", "name_cn": "加州大学洛杉矶分校", "file": "UCLACU", "deptId": 214},
      ...
    }
  }
  ```

### 3. Query Conversation History

- **URL**: `/history/<session_id>`
- **Method**: GET

### 4. Clear Session Records

- **URL**: `/clear/<session_id>`
- **Method**: DELETE

### 5. Health Check

- **URL**: `/health`
- **Method**: GET

---

## App Integration Guide

### Call Flow

```
1. User logs into App
       ↓
2. Call /app/user/info to get user info
       ↓
3. Extract deptId (e.g., 214)
       ↓
4. When user asks question, send request to /ask:
   {
     "question": "user's question",
     "deptId": 214
   }
       ↓
5. Handle response, display answer
```

### Sample Code

```javascript
// Get deptId from user info
const userInfo = await getUserInfo();
const deptId = userInfo.deptId;  // e.g., 214

// Ask AI
const response = await fetch('http://your-server:8087/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: 'When is the housing application deadline?',
        deptId: deptId
    })
});

const data = await response.json();

// Handle response
if (data.source_type === 'web_search' && data.web_sources) {
    // Handle web search citations
    let answer = data.answer.replace(/\[(\d+)\]/g, '<sup>[$1]</sup>');
    showSourceCards(data.web_sources.search_results);
}
```

---

## Frontend Demo

The project includes a test frontend page `index.html`:

1. After starting the service, open `index.html` in browser
2. Select school from dropdown (only shows schools with deptId)
3. Enter question or click quick question buttons
4. View AI answer, source type and citation links

### Frontend Features
- School selector dropdown (auto-filters schools with deptId)
- Modern chat bubble interface
- Source type badges (📚 Knowledge Base / 🌐 Web Search)
- RAG relevance percentage display
- Web search source cards (clickable links)

---

## Common Issues

### 1. "400 Bad Request: deptId cannot be empty"

Add `deptId` parameter to your request:
```json
{
  "question": "your question",
  "deptId": 214
}
```

### 2. "School not found for department ID"

Ensure using correct deptId. Available deptIds: 211, 213, 214, 216, 218, 226

### 3. Why did my question trigger web search?

When question relevance to knowledge base is low (`rag_score < 0.5`), the system automatically enables web search.

---

## Documentation

- [API Documentation](API_DOCUMENTATION.md)
- [RAG Update Notes](RAG_UPDATE.md)
- [Project Structure](PROJECT_STRUCTURE.md)

## Notes

1. Keep your API Key secure
2. Each Q&A consumes Embedding and Rerank API quota
3. Web search consumes additional search API quota
4. Session data is stored in memory and will be lost on restart
5. Do not delete the `vector_store/` directory - it contains the vectorized knowledge base
