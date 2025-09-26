## External API Guide: Java Backend and LLM Service

### About this guide

These APIs are documented with the RAG Studio UI’s data model and flows in mind (Projects, Data Sources/Knowledge Bases, Sessions, Documents). While they are usable externally, some endpoints were designed primarily for the UI and may evolve. Always consult the Swagger/OpenAPI for the latest contract. Refer to [this notebook](rag-api-test.ipynb) for an end-to-end workflow example.

Key notes for external integrations

- Authentication: Every request requires `Authorization: Bearer <API/Application key>` with access to the AI Workbench Application. The platform may inject `origin-remote-user`; you can add `remote-user` when acting on behalf of a specific user.
- Base URLs: Use a single CML host. Java API lives under `/api/v1/rag`, LLM service under `/llm-service` on the same host.
- File uploads: Endpoint accepts a single form part named `file`. To upload many files at once, zip them first. Large files take longer to index.
- Models: List available LLM/embedding/reranking models from the LLM service before creating a data source or session.
- Idempotency: Uploads are not idempotent; re-indexing replaces chunks for a given `doc_id`. Avoid duplicate uploads unless intended.
- Rate limits/timeouts: SSE calls can be long-lived; use generous client timeouts and backoff on retries.
- Scope/ownership: Most Java endpoints return resources for the calling user (via `remote-user`).
- Experimental features: Tool calling is powerful but risky; enable only for trusted tools and least-privileged keys.

This guide shows how to use the Java backend and the LLM service APIs directly to build external integrations. It covers the end-to-end workflow: create a project, create a knowledge base (data source), add documents, create a chat session bound to the knowledge base, and chat.

- Java API base URL: https://<your-cml-host>/api/v1/rag
- LLM Service base URL: https://<your-cml-host>/llm-service
- Swagger UIs:
  - Java: https://<your-cml-host>/swagger-ui/index.html
  - LLM Service: https://<your-cml-host>/llm-service/docs

## Setup

### Using a hosted CML AI Workbench base URL

If the application is deployed on Cloudera CML AI Workbench, you will get a single base link such as:

`https://<your-app-url-on-cml-workbench>`

Use the same host for both services:

- Java API: `https://<your-host>/api/v1/rag/...`
- LLM Service: `https://<your-host>/llm-service/...`

Quick examples with the hosted base URL

```bash
# Set your hosted base URL (no ports)
BASE='https://<your-cml-host>'
API_KEY='<your-api-or-app-key>'

# Create project (Java)
curl -sS -X POST \
  "$BASE/api/v1/rag/projects" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{"name": "My KB"}'

# Stream chat (LLM Service)
curl -N -sS -X POST \
  "$BASE/llm-service/sessions/42/stream-completion" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{"query": "What does the document say about X?"}'
```

### Python requests setup

```python
import requests

BASE = "https://<your-cml-host>"

# Authorization is required (even on the same CML Workbench)
API_KEY = "<your-api-or-app-key>"  # must have access to the AI Workbench Application

# Base headers for auth only (no content type)
auth_headers = {"Authorization": f"Bearer {API_KEY}"}

# JSON headers for typical POST/PUT requests
json_headers = {**auth_headers, "Content-Type": "application/json"}

# Convenience: include a specific user when needed (optional on CML)
headers_with_user = {**json_headers, "remote-user": "alice"}
multipart_headers_with_user = {**auth_headers, "remote-user": "alice"}
# Default headers used in examples below
headers = headers_with_user
```

### Notes for CML deployments

- Do not include localhost ports (8080/8081). Use the single CML base URL.
- The LLM service always lives under the `/llm-service` path prefix on the same host.
- The Java API remains under `/api/v1/rag` on the same host.

### Authentication and headers

- Java backend associates requests with a user by headers:
  - remote-user: <username> (preferred) or origin-remote-user
  - When invoked from the same CML Workbench, the platform typically injects `origin-remote-user` automatically, so the `remote-user` header is optional.
- Authorization
  - Required for all API calls, including from the same CML Workbench: `Authorization: Bearer <API/Application key>`.
  - The API/Application key must have access to the AI Workbench Application hosting this app.
  - In some environments this key may be provided via `CDSW_APIV2_KEY`; otherwise use a key provisioned with appropriate permissions.

### Models and IDs

### Health check

```bash
curl -sS "$BASE/" -H "Authorization: Bearer $API_KEY"
```

```python
resp = requests.get(f"{BASE}/", headers=auth_headers)
resp.raise_for_status()
```

- Terminology: Knowledge Base and Data Source refer to the same concept.
- Project: A container for knowledge bases (data sources) and sessions.
- Data Source (Knowledge Base): Holds documents and model settings (embedding/summarization, chunking).
- Session: A chat session scoped to one or more data sources and a project.
- Documents: Files uploaded to a data source (knowledge base), then indexed by the LLM service.

---

## Projects

### Create a project (Optional)

Request

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/projects" \
  -H 'Content-Type: application/json' \
  -H 'remote-user: alice' \
  -d '{
    "name": "My KB"
  }'
```

Python (create project)

```python
import requests

resp = requests.post(
    f"{BASE}/api/v1/rag/projects",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice", "Content-Type": "application/json"},
    json={"name": "My Project"},
)
resp.raise_for_status()
project = resp.json()
print(project["id"], project["name"])  # e.g., 1, "My Project"
```

Response (example)

```json
{
  "id": 1,
  "name": "My KB",
  "defaultProject": false,
  "timeCreated": 1727300000,
  "timeUpdated": 1727300000,
  "createdById": "alice",
  "updatedById": "alice"
}
```

### Use the default project

If you prefer not to create a project, use the built-in default project. Fetch it and use its `id` for subsequent steps (attaching data sources, creating sessions):

```bash
curl -sS \
  "$BASE/api/v1/rag/projects/default" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice'
```

Python (get default project)

```python
resp = requests.get(
    f"{BASE}/api/v1/rag/projects/default",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
)
resp.raise_for_status()
default_project = resp.json()
print(default_project["id"])  # use for attaching data sources and sessions
```

### List all projects

```bash
curl -sS \
  "$BASE/api/v1/rag/projects" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice'
```

Python

```python
resp = requests.get(
    f"{BASE}/api/v1/rag/projects",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
)
resp.raise_for_status()
projects = resp.json()
```

## Models

### List available models (LLM, embeddings, reranking)

Before creating a data source, fetch available model names from the LLM service to populate `embeddingModel` and (optionally) `summarizationModel` (LLM inference) and `rerankModel`.

```bash
# Model source (e.g., CAII, Bedrock, OpenAI, Azure)
curl -sS \
  "$BASE/llm-service/models/model_source" \
  -H "Authorization: Bearer $API_KEY"

# List LLM (inference) models
curl -sS \
  "$BASE/llm-service/models/llm" \
  -H "Authorization: Bearer $API_KEY"

# List embedding models
curl -sS \
  "$BASE/llm-service/models/embeddings" \
  -H "Authorization: Bearer $API_KEY"

# List reranking models
curl -sS \
  "$BASE/llm-service/models/reranking" \
  -H "Authorization: Bearer $API_KEY"
```

Python (list available models)

```python
# Model source
resp = requests.get(f"{BASE}/llm-service/models/model_source", headers=auth_headers)
resp.raise_for_status()
model_source = resp.json()

# LLM (inference) models
resp = requests.get(f"{BASE}/llm-service/models/llm", headers=auth_headers)
resp.raise_for_status()
llm_models = resp.json()

# Embedding models
resp = requests.get(f"{BASE}/llm-service/models/embeddings", headers=auth_headers)
resp.raise_for_status()
embedding_models = resp.json()

# Reranking models
resp = requests.get(f"{BASE}/llm-service/models/reranking", headers=auth_headers)
resp.raise_for_status()
reranking_models = resp.json()

# Example: pick first model ids (adjust selection as needed)
print(
    (llm_models[0]["model_id"] if llm_models else None),
    (embedding_models[0]["model_id"] if embedding_models else None),
    (reranking_models[0]["model_id"] if reranking_models else None),
)
```

## Data Sources (Knowledge Bases)

### Create a data source (knowledge base configuration)

Request

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/dataSources" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{
    "name": "my-ds",
    "embeddingModel": "text-embedding-3-large",
    "summarizationModel": "gpt-4o-mini",
    "chunkSize": 512,
    "chunkOverlapPercent": 10,
    "connectionType": "MANUAL"
  }'
```

Python (create data source)

```python
resp = requests.post(
    f"{BASE}/api/v1/rag/dataSources",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice", "Content-Type": "application/json"},
    json={
        "name": "my-ds",
        "embeddingModel": "text-embedding-3-large",
        "summarizationModel": "gpt-4o-mini",
        "chunkSize": 512,
        "chunkOverlapPercent": 10,
        "connectionType": "MANUAL",
    },
)
resp.raise_for_status()
ds = resp.json()
print(ds["id"], ds["name"])  # e.g., 10, "my-ds"
```

Response (example)

```json
{
  "id": 10,
  "name": "my-ds",
  "embeddingModel": "text-embedding-3-large",
  "summarizationModel": "gpt-4o-mini",
  "chunkSize": 512,
  "chunkOverlapPercent": 10,
  "timeCreated": 1727300000,
  "timeUpdated": 1727300000,
  "createdById": "alice",
  "updatedById": "alice",
  "connectionType": "MANUAL",
  "documentCount": 0,
  "totalDocSize": 0,
  "availableForDefaultProject": false,
  "associatedSessionId": null
}
```

### (Optional) List all data sources

```bash
curl -sS \
  "$BASE/api/v1/rag/dataSources" \
  -H "Authorization: Bearer $API_KEY"
```

Python

```python
resp = requests.get(
    f"{BASE}/api/v1/rag/dataSources",
    headers={"Authorization": f"Bearer {API_KEY}"},
)
resp.raise_for_status()
data_sources = resp.json()
```

### (Optional) Attach data source to a project

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/projects/1/dataSources/10"
  -H "Authorization: Bearer $API_KEY"
```

Python (attach data source)

```python
project_id = default_project.get("id", 1)
ds_id = ds["id"]
resp = requests.post(
    f"{BASE}/api/v1/rag/projects/{project_id}/dataSources/{ds_id}",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
)
resp.raise_for_status()
```

Note: If you are using the default project, replace `1` with the `id` returned by `GET /api/v1/rag/projects/default`.

### Upload documents to the data source (Java backend)

- Endpoint (multipart): POST /api/v1/rag/dataSources/{dataSourceId}/files
  Request

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/dataSources/10/files" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -F 'file=@/path/to/your.pdf'
```

Python (upload document)

```python
files = {"file": open("/path/to/your.pdf", "rb")}
resp = requests.post(
    f"{BASE}/api/v1/rag/dataSources/{ds_id}/files",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
    files=files,
)
resp.raise_for_status()
documents = resp.json()
doc_id = documents[0]["documentId"]
```

Response (example)

```json
[
  {
    "fileName": "your.pdf",
    "documentId": "doc-123",
    "extension": "pdf",
    "sizeInBytes": 102400
  }
]
```

### Check indexing status

Uploads automatically enqueue indexing. You can poll document status to see when indexing completes.

```bash
curl -sS \
  "$BASE/api/v1/rag/dataSources/10/files" \
  -H "Authorization: Bearer $API_KEY"
```

Python (check indexing status)

```python
resp = requests.get(
    f"{BASE}/api/v1/rag/dataSources/{ds_id}/files",
    headers={"Authorization": f"Bearer {API_KEY}"},
)
resp.raise_for_status()
docs = resp.json()
# Example fields per document: indexingStatus, indexingError, vectorUploadTimestamp
```

### Notes

- Upload triggers indexing automatically. To force a re-index or apply a custom chunk configuration, you may call `POST /llm-service/data_sources/{data_source_id}/documents/{doc_id}/index` with a configuration payload.
- The Java backend stores uploaded files using its configured storage (local or S3-compatible). The LLM service downloads using the provided bucket/key to index. The exact bucket/key must reference where Java stored the file.
- Alternatively, you can call the LLM service summarization endpoints:
  - GET /llm-service/data_sources/{id}/documents/{doc_id}/summary
  - POST /llm-service/data_sources/{id}/documents/{doc_id}/summary

## Sessions

### Create a chat session bound to the project and data source

- Endpoint: POST /api/v1/rag/sessions
- Body fields (CreateSession): name, dataSourceIds, inferenceModel, embeddingModel (optional to create a session-linked DS), rerankModel, responseChunks, queryConfiguration, projectId
  Request

Note: If you did not create a project, set `projectId` to the `id` of the default project from `GET /api/v1/rag/projects/default`.

### List existing sessions

List all sessions for the current user.

```bash
curl -sS \
  "$BASE/api/v1/rag/sessions" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice'
```

Python

```python
resp = requests.get(
    f"{BASE}/api/v1/rag/sessions",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
)
resp.raise_for_status()
all_sessions = resp.json()
```

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/sessions" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{
    "name": "My Session",
    "dataSourceIds": [10],
    "projectId": 1,
    "inferenceModel": "gpt-4o-mini",
    "rerankModel": "bge-reranker",
    "responseChunks": 8,
    "queryConfiguration": {
      "enableHyde": false,
      "enableSummaryFilter": false,
      "enableToolCalling": false,
      "disableStreaming": false,
      "selectedTools": []
    }'
```

Python (create session)

```python
query_configuration = {
    "enableHyde": False,
    "enableSummaryFilter": False,
    "enableToolCalling": False,    # enable at your own risk
    "disableStreaming": False,
    "selectedTools": [],
}
session_payload = {
    "name": "My Session",
    "dataSourceIds": [ds_id],
    "projectId": project_id,
    "inferenceModel": "gpt-4o-mini",    # should be a model from list of llm models
    "rerankModel": None,    # should be a model from the list reranking models or None
    "responseChunks": 8,
    "queryConfiguration": query_configuration,
}
resp = requests.post(
    f"{BASE}/api/v1/rag/sessions",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice", "Content-Type": "application/json"},
    json=session_payload,
)
resp.raise_for_status()
session = resp.json()
session_id = session["id"]
```

Response (example)

```json
{
  "id": 42,
  "name": "My Session",
  "dataSourceIds": [10],
  "projectId": 1,
  "inferenceModel": "gpt-4o-mini",
  "rerankModel": "bge-reranker",
  "responseChunks": 8,
  "queryConfiguration": {
    "enableHyde": false,
    "enableSummaryFilter": false,
    "enableToolCalling": false,
    "disableStreaming": false,
    "selectedTools": []
  }
}
```

### Get an existing session by id

```bash
curl -sS \
  "$BASE/api/v1/rag/sessions/42" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice'
```

Python

```python
resp = requests.get(
    f"{BASE}/api/v1/rag/sessions/{session_id}",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
)
resp.raise_for_status()
session = resp.json()
```

### Update an existing session

Use this to rename a session, change models, toggle features (e.g., tool calling), or update `selectedTools`.

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/sessions/42" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{
    "id": 42,
    "name": "My Updated Session",
    "dataSourceIds": [10],
    "projectId": 1,
    "inferenceModel": "gpt-4o-mini",
    "rerankModel": null,
    "responseChunks": 8,
    "queryConfiguration": {
      "enableHyde": false,
      "enableSummaryFilter": false,
      "enableToolCalling": true,
      "disableStreaming": false,
      "selectedTools": ["<tool-name-1>"]
    }'
```

Python

```python
updated = session.copy()
updated["name"] = "My Updated Session"
updated["queryConfiguration"].update({
    "enableToolCalling": True,
    "selectedTools": tool_names[:1],
})

resp = requests.post(
    f"{BASE}/api/v1/rag/sessions/{session_id}",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice", "Content-Type": "application/json"},
    json=updated,
)
resp.raise_for_status()
session = resp.json()
```

### Chat with the session via LLM service

- Streaming (recommended): POST /llm-service/sessions/{session_id}/stream-completion
- Non-streaming : POST /llm-service/sessions/{session_id}/stream-completion with updated session with `disableStreaming` of `queryConfiguration` as `true`

#### Request (streaming)

```bash
curl -N -sS -X POST \
  "$BASE/llm-service/sessions/42/stream-completion" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{
    "query": "What does the document say about X?",
    "configuration": {
      "exclude_knowledge_base": false,
      "use_question_condensing": true
    }'
```

#### Python (stream chat)

```python

query_configuration = {
        "exclude_knowledge_base": False,
        "use_question_condensing": True,
    }
query_payload = {
    "query": "What benefits does cloudera offer?",
    "configuration": query_configuration,
}

response = requests.post(
    f"{BASE}/llm-service/sessions/{session_id}/stream-completion",
    headers=headers,
    json=query_payload,
    stream=True,
)

text = ""
resp_id = None
for resp_chunk in response:
    decoded_resp_chunk = resp_chunk.decode('utf-8')
    decoded_resp_json = json.loads(decoded_resp_chunk.replace("data:", "").strip())
    if 'text' in decoded_resp_json:
        text += decoded_resp_json['text']
        print(decoded_resp_json['text'], end="")
    if 'response_id' in decoded_resp_json:
        resp_id = decoded_resp_json['response_id']
print("===========")
print(f"Response ID: {resp_id}, Text: {text}")
```

#### Non-streaming chat (disable streaming)

To use non-streaming responses (as in the notebook), first update the session to set `queryConfiguration.disableStreaming = true`, then call the same chat endpoint and fetch the full response from chat history using the `response_id`.

Step 1: Update session to disable streaming

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/sessions/42" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{
    "id": 42,
    "name": "My Session",
    "dataSourceIds": [10],
    "projectId": 1,
    "inferenceModel": "gpt-4o-mini",
    "rerankModel": null,
    "responseChunks": 8,
    "queryConfiguration": {
      "enableHyde": false,
      "enableSummaryFilter": false,
      "enableToolCalling": false,
      "disableStreaming": true,
      "selectedTools": []
    }
  '
```

Step 2: Call chat and capture `response_id`, then fetch the full message

```bash
curl -N -sS -X POST \
  "$BASE/llm-service/sessions/42/stream-completion" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{
    "query": "What benefits does cloudera offer?",
    "configuration": {"exclude_knowledge_base": false, "use_question_condensing": true}
  }'

# Then fetch full response by id (replace $RESP_ID)
curl -sS \
  "$BASE/llm-service/sessions/42/chat-history/$RESP_ID" \
  -H "Authorization: Bearer $API_KEY"
```

Python

```python
# 1) Disable streaming on the session
updated = session.copy()
updated["queryConfiguration"]["disableStreaming"] = True
resp = requests.post(
    f"{BASE}/api/v1/rag/sessions/{session_id}",
    headers=headers,
    json=updated,
)
resp.raise_for_status()

# 2) Call chat, capture response_id, then fetch full message by id
query_configuration = {
    "exclude_knowledge_base": False,
    "use_question_condensing": True,
}
query_payload = {
    "query": "What about upskilling for cloudera employees?",
    "configuration": query_configuration,
}

response = requests.post(
    f"{BASE}/llm-service/sessions/{session_id}/stream-completion",
    headers=headers,
    json=query_payload,
    stream=True,
)

resp_id_ns = None
last_chunk = None
for resp_chunk in response:
    decoded = resp_chunk.decode("utf-8").strip()
    if not decoded:
        continue
    last_chunk = decoded
    try:
        evt = json.loads(decoded.replace("data:", ""))
        if "response_id" in evt:
            resp_id_ns = evt["response_id"]
    except Exception:
        continue

# If not captured in the loop, try reading the last chunk
if resp_id_ns is None and last_chunk:
    resp_id_ns = json.loads(last_chunk.replace("data:", ""))["response_id"]

# Fetch the full message
resp = requests.get(
    f"{BASE}/llm-service/sessions/{session_id}/chat-history/{resp_id_ns}",
    headers=auth_headers,
)
resp.raise_for_status()
message_ns = resp.json()
```

### Rename session using AI

After the first message, you can ask the system to generate a descriptive session name.

```bash
curl -sS -X POST \
  "$BASE/llm-service/sessions/42/rename-session" \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice'
```

Python

```python
resp = requests.post(
    f"{BASE}/llm-service/sessions/{session_id}/rename-session",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
)
resp.raise_for_status()
new_name = resp.text.strip()
print(new_name)
```

### Retrieve response information

After receiving a response, you can fetch detailed information about it using the response ID.

```bash
# Get a single message (response) by ID
curl -sS \
  "$BASE/llm-service/sessions/42/chat-history/$RESP_ID" \
  -H "Authorization: Bearer $API_KEY"
```

Python

```python
# Single message by id
resp = requests.get(
    f"{BASE}/llm-service/sessions/{session_id}/chat-history/{resp_id}",
    headers={"Authorization": f"Bearer {API_KEY}"},
)
resp.raise_for_status()
message = resp.json()
```

### Get source node information

Each chat message includes `source_nodes` with the retrieval hits for that response. You can also fetch the full contents of a source chunk.

```bash
# Fetch the message and inspect its source_nodes
curl -sS \
  "$BASE/llm-service/sessions/42/chat-history/$RESP_ID" \
  -H "Authorization: Bearer $API_KEY"

# Given a source node, retrieve chunk contents (node_id == chunk_id)
# Replace <data_source_id> with the node's dataSourceId and <chunk_id> with node_id
curl -sS \
  "$BASE/llm-service/data_sources/<data_source_id>/chunks/<chunk_id>" \
  -H "Authorization: Bearer $API_KEY"
```

Python

```python
# Get source nodes from the message
resp = requests.get(
    f"{BASE}/llm-service/sessions/{session_id}/chat-history/{resp_id}",
    headers={"Authorization": f"Bearer {API_KEY}"},
)
resp.raise_for_status()
msg = resp.json()
nodes = msg.get("source_nodes", [])  # [{node_id, doc_id, source_file_name, score, dataSourceId}]

# Fetch chunk contents for the first node
if nodes:
    ds_id = nodes[0].get("dataSourceId")
    chunk_id = nodes[0].get("node_id")
    resp = requests.get(
        f"{BASE}/llm-service/data_sources/{ds_id}/chunks/{chunk_id}",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    resp.raise_for_status()
    chunk = resp.json()  # {"text": ..., "metadata": {...}}
```

### Retrieve chat history

```bash
curl -sS \
  "$BASE/llm-service/sessions/42/chat-history"
  -H "Authorization: Bearer $API_KEY"
```

Python (chat history)

```python
resp = requests.get(
    f"{BASE}/llm-service/sessions/{session_id}/chat-history",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice"},
)
resp.raise_for_status()
history = resp.json()
print(history.get("data", []))
```

### Rate or give feedback on a response

```bash
curl -sS -X POST \
  "$BASE/llm-service/sessions/42/responses/<response_id>/rating" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"rating": true}'

curl -sS -X POST \
  "$BASE/llm-service/sessions/42/responses/<response_id>/feedback" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"feedback": "Helpful!"}'
```

Python (rating and feedback)

```python
response_id = "<response_id>"

resp = requests.post(
    f"{BASE}/llm-service/sessions/{session_id}/responses/{response_id}/rating",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={"rating": True},
)
resp.raise_for_status()

resp = requests.post(
    f"{BASE}/llm-service/sessions/{session_id}/responses/{response_id}/feedback",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={"feedback": "Helpful!"},
)
resp.raise_for_status()
```

## Delete operations

- Java: DELETE /api/v1/rag/dataSources/{id}
- Java: DELETE /api/v1/rag/dataSources/{id}/files/{documentId}
- Java: DELETE /api/v1/rag/sessions/{id}
- LLM: DELETE /llm-service/sessions/{session_id}

## Reference of key endpoints

- Java (CML host)
  - Projects: /api/v1/rag/projects
  - DataSources: /api/v1/rag/dataSources
  - Files: /api/v1/rag/dataSources/{dataSourceId}/files
  - Sessions: /api/v1/rag/sessions
  - Metrics: /api/v1/rag/metrics
- LLM (CML host, root /llm-service)
  - Data source index/delete: /data_sources/{id}/documents/{doc_id}/index, /data_sources/{id}/documents/{doc_id} (DELETE)
  - Data source summaries: /data_sources/{id}/documents/{doc_id}/summary, /data_sources/{id}/summary
  - Sessions: /sessions/{session_id}/chat, /sessions/{session_id}/stream-completion, /sessions/{session_id}/chat-history
  - Models: /models/llm, /models/embeddings, /models/reranking

## Notes and caveats

- Ensure the LLM service can access the same storage location used by the Java backend for uploaded documents (bucket/key). In local dev, this may be a local/simulated S3 path.
- Provide remote-user where possible to preserve per-user scoping in Java.
- For production, configure proper auth. The code paths show token forwarding for internal calls; external callers should secure endpoints behind your gateway and supply appropriate headers.

## Experimental: Tool calling (try at your own risk)

Tool calling allows the model to invoke external tools during chat. Try at your own risk. Enable only if you trust the tools and their permissions. Use least-privileged keys and audit tool definitions.

List available tools (for `selectedTools`)

```bash
curl -sS \
  "$BASE/llm-service/tools" \
  -H "Authorization: Bearer $API_KEY"
```

Python

```python
resp = requests.get(f"{BASE}/llm-service/tools", headers=auth_headers)
resp.raise_for_status()
tools = resp.json()  # each has {"name": "...", "metadata": {...}}
tool_names = [t["name"] for t in tools]
```

Enable tool calling for a session

```bash
curl -sS -X POST \
  "$BASE/api/v1/rag/sessions" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $API_KEY" \
  -H 'remote-user: alice' \
  -d '{
    "name": "My Tool Session",
    "dataSourceIds": [10],
    "projectId": 1,
    "inferenceModel": "gpt-4o-mini",
    "rerankModel": "bge-reranker",
    "responseChunks": 8,
    "queryConfiguration": {
      "enableHyde": false,
      "enableSummaryFilter": false,
      "enableToolCalling": true,
      "disableStreaming": false,
      "selectedTools": ["<tool-name-1>", "<tool-name-2>"]
    }'
```

Python

```python
session_payload["queryConfiguration"].update(
    {
        "enableToolCalling": True,
        "selectedTools": tool_names[:2],  # choose specific trusted tools
    }
)
resp = requests.post(
    f"{BASE}/api/v1/rag/sessions",
    headers={"Authorization": f"Bearer {API_KEY}", "remote-user": "alice", "Content-Type": "application/json"},
    json=session_payload,
)
resp.raise_for_status()
```
