### RAG Studio Quickstart (UI)

#### Table of Contents

- [1) Open the App](#1-open-the-app)
- [2) Create a Knowledge Base](#2-create-a-knowledge-base)
- [3) Upload Documents](#3-upload-documents)
- [4) Start a Chat](#4-start-a-chat)
- [5) Tune Chat Settings (Optional)](#5-tune-chat-settings-optional)
- [6) Use Tools (Beta, Optional)](#6-use-tools-beta-optional)
- [7) Review Analytics (Optional)](#7-review-analytics-optional)
- [Troubleshooting](#troubleshooting)

---

### 1) Open the App

Landing Page:

## ![landing-page](images/landing-page.png)

**Note on Configuration (CML + CAII):**

- If your CML deployment and CAII (Cloudera AI Inference) endpoints (LLM, Embeddings, Rerankers) are in the same environment, the app validates Studio configuration with CAII.
- If no valid configuration is detected, you will be redirected to Settings to configure the Studio.
- For a breakdown of each option, see Studio Settings Configurations in the [UI Guide](rag-studio-ui-guide.md#studio-settings-configurations).

## ![settings-no-data](images/settings-studio-settings-no-data.png)

### 2) Create a Knowledge Base

1. Go to **Knowledge Bases** and click **Create Knowledge Base**.
2. Fill in the required fields: Name, Chunk Size, Embedding Model.
3. Optional: Select a Summarization Model.
4. Click **Save**.

## ![create-kb](images/rag-studio-kb-create-kb.png)

---

### 3) Upload Documents

1. Open the knowledge base and navigate to the **Manage** tab.
2. Drag-and-drop or select files, then click **Start Upload**.
3. Confirm the uploaded files appear in the table.

## ![manage-tab](images/rag-studio-kb-manage-page.png)

---

### 4) Start a Chat

1. Go to **Chats**.
2. In the input box, type a question.
3. Send the message (**Enter** or click send). If no session exists, it will be created automatically on first send.
4. **Optional before sending:** Click **Chat Settings** to open the Create Session modal and preselect knowledge base(s) and response model.

**Tips:**

- Use the KB selector (when creating a new session) next to the input to pick knowledge bases.
- Use the model selector next to the input to choose the response model.
- Toggle the database icon to include or exclude the knowledge base per message.
- Use the stop icon to cancel streaming.
- Click suggested questions to continue the conversation.

**Suggested Questions:**

- If a session is created with no messages, you'll see Suggested Questions in the chat body (KB-aware when KBs are selected; default list if none).
- After you send a message, follow-up suggestions appear after the response.

## ![chat](images/rag-studio-chats-page.png)

## ![follow-up-question](images/suggested-questions-follow-up.png)

---

### 5) Tune Chat Settings (Optional)

1. Click **Chat Settings** in the chat header.
2. Adjust: session name, knowledge bases, response model, rerank model, max docs, and advanced options (Tool Calling, HyDE, Summary Filter, Disable Streaming).
3. Click **Save**.

## ![chat-settings](images/chat-settings-update.png)

---

### 6) Use Tools (Beta, Optional)

- Enable **Tool Calling** from Chat Settings.
- If Tool Calling is enabled, click the wrench icon and select tools.
- Manage available tools in **Settings → Tools**.

## ![select-tool-modal](images/chat-select-tool-modal.png)

---

### 7) Review Analytics (Optional)

1. Open **Analytics**.
2. Review App Metrics and Session Metrics.
3. Filter by model, reranker (or None), summary filter usage, HyDE, knowledge base usage, and project.

## ![analytics-filter](images/rag-studio-analytics-page.png)

## ![analytics-charts](images/rag-studio-analytics-charts.png)

---

### Troubleshooting

- **No embedding models available** when creating a knowledge base → Configure models in **Settings → Model Configuration**.
- **Upload errors** → Check file size/type and retry.
- **Chat not using knowledge base** → Ensure the database icon is filled (included) or select KBs for the session.

## ![kb-selected](images/chat-input-kb-selected.png)

## ![kb-unselected](images/chat-input-kb-unselected.png)
