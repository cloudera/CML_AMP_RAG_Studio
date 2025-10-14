### RAG Studio UI Guide

#### Table of contents

- [Navigation overview](#navigation-overview)
- [Configuration check and redirection (CML + CAII)](#-configuration-check-and-redirection-cml--caii)
- [Knowledge Bases](#knowledge-bases)
  - [Create a knowledge base](#create-a-knowledge-base)
  - [Upload and manage documents](#upload-and-manage-documents)
  - [Edit knowledge base settings](#edit-knowledge-base-settings)
  - [Other knowledge base tabs](#other-knowledge-base-tabs)
- [Chats](#chats)
  - [Start a new chat](#start-a-new-chat)
  - [Ask questions](#ask-questions)
  - [Input controls and quick settings](#input-controls-and-quick-settings)
  - [Use knowledge bases in a chat](#use-knowledge-bases-in-a-chat)
  - [Upload documents to the active chat](#upload-documents-to-the-active-chat)
  - [Suggested questions and sources](#suggested-questions-and-sources)
  - [Chat Settings (session-level)](#chat-settings-session-level)
  - [Inference model quick switch](#inference-model-quick-switch)
  - [Tools (beta)](#tools-beta)
- [Analytics](#analytics)
- [Settings](#settings)
  - [Studio Settings configurations](#studio-settings-configurations)
  - [Add tools from the UI](#add-tools-from-the-ui)

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

### Studio Settings configurations

Use Settings → Studio Settings to configure the application. Some fields are only editable when there are no chats or knowledge bases.

#### Processing Settings

- Enhanced PDF Processing: Improves text extraction for PDFs; requires a GPU and at least 16GB RAM. Disabled with a warning if resources are insufficient.

#### Metadata Database

- Embedded (H2): Default metadata database.
- External PostgreSQL: Provide JDBC URL, Username, Password. Use “Test Connection” to validate; success/failure indicators are shown inline.

## ![external-postgres](images/settings-metadatadb-external-postgres.png)

#### File Storage

- Project Filesystem (Local): Stores files in the project filesystem.
- AWS S3: Set Document Bucket Name and optional Bucket Prefix.
  - Store Document Summaries in S3: Toggle when summarization is enabled for knowledge bases.
  - Store Chat History in S3: Toggle to persist chat history in S3.
  ## ![file-storage-s3](images/settings-file-storage-S3.png)

#### Vector Database

- Qdrant: Embedded Qdrant (default).
- Cloudera Semantic Search (OpenSearch): Set Endpoint, Namespace (alphanumeric), optional Username/Password. Supported up to OpenSearch 2.19.3.

## ![vectordb-css](images/settings-vectordb-css.png)

- ChromaDB: Set Host (URL or host), optional Port, Token, Tenant, Database. SSL inferred from https in host.

## ![vectordb-chromadb](images/settings-vectordb-chromadb.png)

#### Model Provider

Choose a provider (e.g., CAII, OpenAI, Azure, Bedrock). Credentials are set under Authentication.

- CAII

  - If there are no hosted CAII endpoints on the same environment, you can optionally provide one which has hosted endpoints along with the CDP Auth Token

  ## ![model-provider-caii](images/settings-model-provider-caii.png)

- OpenAI

  - API Key: Provide your OpenAI API Key for authentication.
  - Base URL: Optional custom base URL for OpenAI-compatible endpoints.

  ## ![model-provider-openai](images/settings-model-provider-open-ai.png)

- Azure OpenAI

  - API Key: Your Azure OpenAI service API key.
  - Endpoint: The Azure OpenAI service endpoint URL.
  - API Version: The API version to use (e.g., 2024-02-01).

  ## ![model-provider-azure](images/settings-model-provider-azure-openai.png)

- AWS Bedrock
  - Region: AWS region where your Bedrock models are hosted.
  - Access credentials are configured in the Authentication section.
  ## ![model-provider-bedrock](images/settings-model-provider-aws-bedrock.png)

#### Authentication

- AWS: Region, Access Key ID, Secret Access Key (visible when using Bedrock/S3/Summary S3).

## ![authentication-s3-and-or-bedrock](images/settings-authentication-s3-and-or-bedrock.png)

- Azure: Azure OpenAI Key (when Azure is selected).
- OpenAI: OpenAI API Key (when OpenAI is selected).
- CAII: CDP Auth Token may be required depending on environment.

#### Applying changes

- Click Submit to review and confirm. A restart modal guides you to apply changes.

## ![update-settings-modal](images/settings-update-settings-modal.png)

## ![updates-settings-progress](images/settings-update-settings-progress-modal.png)

- If chats or knowledge bases exist, a warning shows and certain settings are disabled until data is removed.

## ![settings-studio](images/settings-studio-settings-data.png)

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
