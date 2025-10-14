### RAG Studio UI Guide

This guide explains how to use RAG Studio entirely from the UI. It focuses on the main navigation, creating and managing knowledge bases, starting chats, tuning chat settings, using tools, and reviewing analytics.

## ![landing-page](images/landing-page.png)

---

### Navigation overview

- **Chats**: Ask questions, manage sessions, upload files to the active chat, and control models/tools.
- **Knowledge Bases**: Create and manage knowledge bases, upload documents, and configure indexing.
- **Analytics**: Review app and session metrics with filters.
- **Settings**: Configure studio settings, models, and tools.

## ![chat](images/rag-studio-chats-page.png)

---

### Configuration check and redirection (CML + CAII)

- If the CML deployment and CAII (Cloudera AI Inference) endpoints for LLM, Embeddings and/or Rerankers are on the same environment, the app validates Studio configuration with CAII.
- If there is no valid configuration, after clicking “Get started”, you will be redirected to the Settings page to configure the Studio.

## ![settings-no-data](images/settings-studio-settings-no-data.png)

## ![settings-data](images/settings-studio-settings-data.png)

---

### Knowledge Bases

#### Create a knowledge base

1. Go to Knowledge Bases.
2. Click “Create Knowledge Base”.
3. Fill in required fields:
   - **Name**
   - **Chunk size (tokens)**
   - **Embedding model** (required to create)
   - Optional: **Summarization model** to enable summary-based retrieval
   - Advanced (optional): **Chunk overlap**, **Distance metric** (Cosine)
4. Save.

## ![kb-list](images/rag-studio-kb-page.png)

## ![create-kb](images/rag-studio-kb-create-kb.png)

#### Upload and manage documents

1. Open a knowledge base → “Manage” tab.
2. Drag-and-drop or select files. Click “Start Upload”.
3. Use the table to view, delete, or summarize documents (if a summarization model is set).

## ![kb-manage](images/rag-studio-kb-manage-page.png)

#### Edit knowledge base settings

1. Open a knowledge base → “Index Settings”.
2. Update fields like name, models, availability, etc.
3. Save with “Update”. Optionally delete the knowledge base.

## ![kb-index-settings](images/rag-studio-kb-index-settings.png)

#### Other knowledge base tabs

- **Connections**: Configure external connectors (if applicable).
- **Metrics**: Knowledge-base level stats.
- **Visualize**: Explore vector graph visualization.

## ![kb-connections](images/rag-studio-kb-connections-page.png)

---

### Chats

#### Start a new chat

Type a question and send. If no session exists, a new session is created automatically on your first send.

Optional: Click “Chat Settings” before sending to open the Create Session modal and preselect knowledge base(s) and the response synthesizer model.

## ![chats-page](images/rag-studio-chats-page.png)

## ![create-session](images/chat-create-session.png)

#### Ask questions

- Use the input box at the bottom. Press Enter to send; Shift+Enter inserts a newline.
- Click the send icon to submit.
- Click the stop icon to cancel a streaming response.
- If knowledge bases exist, the placeholder says “Ask a question”; otherwise “Chat with the LLM”.

## ![input-bar](images/chat-input-bar.png)

#### Input controls and quick settings

- Knowledge base selector: When no session exists, pick one or more knowledge bases next to the input before sending the first message.
- Inference model selector: Choose the response model next to the input. If a session exists, this updates the session; if not, it’s used for the new session.
- Tools (wrench icon): When Tool Calling is enabled, click to open Tool Selection and enable/disable tools for the session.
- Include/exclude knowledge base toggle (database icon): Per-message control to include or exclude knowledge base retrieval.
- Stop streaming button: Appears while a response is streaming.

## ![input-bar](images/chat-input-bar.png)

#### Use knowledge bases in a chat

- Toggle the database icon to include/exclude the knowledge base for the current message.

## ![kb-selected](images/chat-input-kb-selected.png)

## ![kb-unselected](images/chat-input-kb-unselected.png)

- For new sessions, optionally select knowledge base(s) next to the input before sending the first message.

## ![new-chat-kb-select-dd](images/chat-input-add-kb.png)

#### Upload documents to the active chat

- Drag files anywhere in the chat area; a drop overlay appears. Drop to upload into the associated knowledge base for the session.
- Or open the “Documents” control (paperclip/folder) near the input to manage uploads.

## ![documents-icon](images/chat-documents-icon.png)

## ![documents-modal](images/chat-documents-modal.png)

#### Suggested questions and sources

- Empty chat: When a session exists with no messages, Suggested Questions cards appear in the chat body. They are generated from the selected knowledge base(s). If none are selected/available, a default starter list is shown.
- After messages: Follow-up suggestions appear near the input, tailored to the current session. If no knowledge base is in use, a default list is shown.
- Sources and feedback: Each answer shows citations (“Sources”) and optional evaluations (e.g., relevance, faithfulness). Use the copy and rating/feedback controls under each answer.

## ![suggested-kb](images/suggested-questions-kb.png)

## ![suggested-default](images/suggested-questions-default.png)

## ![suggested-follow-up](images/suggested-questions-follow-up.png)

#### Chat Settings (session-level)

Open “Chat Settings” in the header to modify the active session:

- Rename session
- Select knowledge base(s)
- Choose response synthesizer model
- Optional reranking model
- Maximum number of documents
- Advanced options:
  - Tool Calling (beta)
  - HyDE
  - Summary-based filtering
  - Disable streaming

## ![chat-settings](images/chat-settings-update.png)

#### Inference model quick switch

- Next to the input, change the model on-the-fly. If the new model supports tool calling, the session setting updates accordingly.

## ![inference-model](images/chat-inference-model.png)

#### Tools (beta)

- If Tool Calling is enabled, click the wrench icon to open Tool Selection. Check tools to enable for the session.
- Available tools are managed in Settings → Tools.

## ![tools-icon](images/chat-tool-icon.png)

## ![tools-modal](images/chat-select-tool-modal.png)

---

### Analytics

Use the Analytics page to view:

- **App Metrics**: Overall usage and health metrics.
- **Session Metrics**: Filter by response model, rerank model (or None), summary filter usage, HyDE, knowledge-base usage, and project.

## ![analytics-filter](images/rag-studio-analytics-page.png)

## ![analytics-charts](images/rag-studio-analytics-charts.png)

---

### Settings

- **Studio Settings**: Environment and studio configuration.
- **Model Configuration**: Manage embedding and LLM models used across the app.
- **Tools**: Enable and configure tools available for Tool Calling.

## ![settings-studio](images/settings-studio-settings-data.png)

## ![settings-models](images/settings-model-configuration.png)

## ![settings-tools](images/settings-tools-management.png)

### Add tools from the UI

## ![tools-page](images/settings-tools-management.png)

1. Go to Settings → Tools.
2. Click “Add Tool”.
3. In the modal, provide:
   - Internal Name (alphanumeric and dashes)
   - Display Name
   - Description
4. Choose Tool Type:
   - Command-based: enter Command, optional Arguments (comma-separated), and add Environment Variables (key/value) as needed.
        - For eg. to add Serper Search & Scrape MCP -
            ```
            Command - npx
            Arguments - -y, serper-search-scrape-mcp-server
            Environment Variables -
                - SERPER_API_KEY": your_api_key_here
            ```
    ## ![tools-add-command](images/settings-add-tools-command.png)

   - URL-based: enter one or more URLs (comma-separated). (Not recommended)
    ## ![tools-add-url](images/settings-add-tools-url.png)
5. Click “Add”. The tool appears in the Available Tools table (you can delete it later).
6. To use a tool in chat, enable Tool Calling in Chat Settings, then click the wrench icon in the input bar and select the tool(s).


---
