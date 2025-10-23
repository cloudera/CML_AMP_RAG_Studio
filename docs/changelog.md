### RAG Studio Changelog (release/1)

This changelog summarizes notable changes per tagged release from 1.0.0 through 1.30.0 on the release/1 branch.

#### Table of Contents

- [1.31.0](#1310)
- [1.30.0](#1300)
- [1.29.0](#1290)
- [1.28.1](#1281)
- [1.28.0](#1280)
- [1.27.0](#1270)
- [1.26.0](#1260)
- [1.25.0](#1250)
- [1.24.1](#1241)
- [1.24.0](#1240)
- [1.23.0](#1230)
- [1.22.2](#1222)
- [1.22.1](#1221)
- [1.22.0](#1220)
- [1.21.0](#1210)
- [1.20.0](#1200)
- [1.19.0](#1190)
- [1.18.0](#1180)
- [1.17.0](#1170)
- [1.16.0](#1160)
- [1.15.0](#1150)
- [1.14.0](#1140)
- [1.13.0](#1130)
- [1.12.0](#1120)
- [1.11.0](#1110)
- [1.10.0](#1100)
- [1.9.0](#190)
- [1.8.0](#180)
- [1.7.0](#170)
- [1.6.0](#160)
- [1.5.0](#150)
- [1.4.2](#142)
- [1.4.1](#141)
- [1.4.0](#140)
- [1.3.0](#130)
- [1.2.0](#120)
- [1.1.0](#110)
- [1.0.0](#100)

## 1.31.0

- Added Excel (.xlsx) file support for document ingestion
- Enhanced indexing performance for tabular documents (CSV, Excel)
- Updated dependencies and internal improvements

## 1.30.0

- Added ChromaDB support
- Multi-slide `.pptx` files are now fully ingested instead of just the first slide

## 1.29.0

- Added `TEXT_TO_TEXT_GENERATION` model support as inference models
- Cleaned up model provider detection and environment handling
- Deprecated `/chat` endpoint in favor of `/stream-completion`

## 1.28.1

- Emergency fixes and enhancements
- Pinned OpenSearch versions and added UI note; improved validation

## 1.28.0

- Implemented download file link in UI
- Updated dependencies and added GPT-5 to OpenAI models
- Removed unused describeEndpoint fields

## 1.27.0

- Aggregate maintenance updates (Mob/main)

## 1.26.0

- Added script to restore the global summary index
- Improved CAII model discovery and pre-release fixes

## 1.25.0

- Chat UI improvements
- Miscellaneous dependency updates and stability tweaks

## 1.24.1

- Fixed handling of empty knowledge base in chat flows

## 1.24.0

- Added ability to upload files directly to a chat session
- Reverted MLflow to 2.x and corrected run UUID key

## 1.23.0

- Replaced crew with custom Tool Calling implementation
- Streaming chat cleanup and in-process Docling
- Saved artifacts in repository instead of release assets
- Added fake-streaming for non-streaming tool models; enabled tool calling by default for subset
- New Tools Manager UI

## 1.22.2

- Hotfixes and dependency bumps

## 1.22.1

- Fixed: Kill startup script if Python fails to start

## 1.22.0

- Added OpenSearch (Cloudera Semantic Search) vector database support
- Added multi-knowledge base support in sessions
- Allowed canceling in-flight chat requests from UI
- Made data source IDs optional on create session; filtered unsupported Bedrock models

## 1.21.0

- Added Tool Calling feature (initial release)

## 1.20.0

- Added OpenAI support and model provider
- Cross-config fixes and base URL tweaks

## 1.19.0

- Allowed providing a CDP token for CAII access

## 1.18.0

- Added streaming responses in chat; copy-to-clipboard for answers
- Fixed config update logic and type fallbacks
- Removed Qdrant as a separate app; returned to single-app mode

## 1.17.0

- Added current release version display in UI; service URL handling improvements
- Optional OpenSearch startup for local dev; vector store factory refactor
- CORS/auth improvements across Node/Java/Python; service URL discovery and health checks

## 1.16.0

- Added Qdrant as a separate app; summary storage options (S3/Local) in Settings
- Environment validation; "Get Started" redirect to Settings when invalid
- CAII wording/readme updates

## 1.15.0

- Analytics: filter by Project ID
- Ability to move chat sessions between projects
- Feedback/ratings UX tweaks

## 1.14.0

- Combined Java/Python Swagger; proxy improvements and linting/mypy fixes

## 1.13.0

- Pre-release polish; UI/Swagger routing updates

## 1.12.0

- KB-free chat sessions; new session-free chat flows
- Projects (foundation): CRUD endpoints and initial UI scaffolding
- Suggested questions improvements and session/KB wiring

## 1.11.0

- CAII: prefer NVIDIA models where appropriate; summarization tuning
- NiFi template authentication header support; multi-configuration support

## 1.10.0

- Added Azure model provider; Bedrock ARN regional support
- Refactored model provider interfaces and tests

## 1.9.0

- Added analytics and metrics dashboards (App + Session metrics)
- Response ratings and feedback; markdown rendering for answers

## 1.8.0

- Added CAII DeepSeek support
- Session advanced options: HyDE, summary filter, condensing toggles

## 1.7.0

- Added reranking end-to-end (UI, session model, post-processors)
- Two-stage retrieval options and condensing enhancements

## 1.6.0

- Composability: optional top navigation for composed environments
- Chunk retrieval strategy tuning and early evaluation framework
- Simple reranker and retriever refactor; Node server migrated to TypeScript

## 1.5.0

- Markdown responses; image handling (Docling JPG/PNG)
- Enhanced parsing option; robust error handling in indexing/reconciliation

## 1.4.2

- Maintenance: mob/main merge and small fixes

## 1.4.1

- Minor fixes and model status improvements

## 1.4.0

- CAII endpoint discovery; batch embeddings for CAII
- Multiple embedding models per knowledge base
- Local filesystem storage path support

## 1.3.0

- CSV/JSON parsing with row linking; UI shows row numbers
- Docling PDF support; added PDF page numbers display
- Visualization and PowerPoint support; switched to UV for Python dependencies

## 1.2.0

- Indexing service abstraction and stability improvements
- CI: ruff/mypy; ensured single indexing on long runs

## 1.1.0

- UI and backend refinements; reconciler improvements and deprecations

## 1.0.0

- Initial GA release on release/1
- Java backend migration and cloud configuration API
- Python migrator for SQLite; document deletion; early tests for Qdrant/models
