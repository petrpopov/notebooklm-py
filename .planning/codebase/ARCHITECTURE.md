# Architecture

**Analysis Date:** 2026-03-15

## Pattern Overview

**Overall:** Layered async client with domain-driven API namespacing and RPC protocol abstraction.

**Key Characteristics:**
- Four-layer design: RPC → Core → Client → CLI
- Namespaced sub-client APIs (notebooks, sources, artifacts, chat, notes, research, settings, sharing)
- Async-first with httpx for HTTP operations
- RPC protocol encapsulation for Google's undocumented batchexecute API
- Context manager pattern for resource lifecycle (`async with NotebookLMClient`)

## Layers

**RPC Layer (Protocol):**
- Purpose: Encode RPC requests, decode responses, handle protocol-level errors
- Location: `src/notebooklm/rpc/`
- Contains: Method ID enums, request encoding, response parsing, error codes
- Depends on: Nothing (pure protocol layer)
- Used by: Core layer exclusively
- Key files:
  - `types.py`: RPCMethod enum (obfuscated method IDs), artifact/audio/video enums
  - `encoder.py`: Builds triple-nested JSON structures for batchexecute
  - `decoder.py`: Parses chunked responses, extracts RPC results

**Core Layer (Infrastructure):**
- Purpose: HTTP client lifecycle, RPC call orchestration, auth token management, caching
- Location: `src/notebooklm/_core.py`
- Contains: `ClientCore` class managing httpx.AsyncClient, RPC call wrapping, token refresh
- Depends on: RPC layer for encoding/decoding
- Used by: All domain API classes
- Key responsibilities:
  - HTTP client open/close with granular timeouts
  - RPC call execution with automatic auth token refresh on failure
  - CSRF token and session ID header management
  - Conversation turn caching (FIFO eviction at 100 items)
  - Source ID extraction helper for cross-API use

**Client Layer (Domain APIs):**
- Purpose: Domain-specific operations exposed through namespaced sub-clients
- Location: `src/notebooklm/` with `_*.py` suffix convention
- Contains: NotebooksAPI, SourcesAPI, ArtifactsAPI, ChatAPI, NotesAPI, ResearchAPI, SettingsAPI, SharingAPI
- Depends on: Core layer exclusively
- Used by: CLI layer and direct Python API consumers
- Pattern: Each API class takes `ClientCore` in `__init__`, uses `_core.rpc_call()` for all operations
- Key methods follow async convention: `async def list()`, `async def create()`, etc.
- Examples:
  - `_notebooks.py`: `NotebooksAPI(core)` with `.list()`, `.create()`, `.rename()`, `.delete()`, `.get_description()`
  - `_sources.py`: `SourcesAPI(core)` with `.add_url()`, `.add_youtube()`, `.add_text()`, `.list()`, `.delete()`, `.rename()`
  - `_chat.py`: `ChatAPI(core)` with `.ask()` supporting conversations and source filtering
  - `_artifacts.py`: `ArtifactsAPI(core)` with `.generate_*()` for all types, `.list()`, `.wait_for_completion()`, `.download()`

**Client Entry Point:**
- Purpose: Assembles all sub-client APIs into single cohesive interface
- Location: `src/notebooklm/client.py`
- Contains: `NotebookLMClient` class
- Initialization: Creates `ClientCore`, then initializes all sub-clients, passing core to each
- Context manager: `async with NotebookLMClient.from_storage()` handles open/close
- Key pattern: `NotebookLMClient(auth)` or `NotebookLMClient.from_storage(path)` factory

**CLI Layer (Command Interface):**
- Purpose: Click-based command hierarchy for shell automation
- Location: `src/notebooklm/cli/` with modular command files
- Contains: Command groups (source, artifact, generate, download, note, etc.) and register functions (session, notebook, chat)
- Depends on: Client layer for actual operations
- Entry point: `src/notebooklm/notebooklm_cli.py` with main `cli()` group
- Pattern: Commands invoke `@with_client` decorator to get client, then call client APIs

## Data Flow

**Authentication Flow:**

1. User runs `notebooklm login` → Playwright browser automation
2. Browser captures cookies and CSRF tokens after Google auth
3. Tokens saved to `~/.notebooklm/storage_state.json`
4. `AuthTokens.from_storage()` loads tokens on demand
5. `ClientCore` includes tokens in HTTP headers (Cookie, CSRF headers)

**RPC Call Flow:**

1. CLI command or Python code calls domain API (e.g., `client.notebooks.list()`)
2. Domain API builds params list and calls `_core.rpc_call(RPCMethod.X, params)`
3. `ClientCore` encodes params using `encode_rpc_request()` → triple-nested JSON
4. HTTP POST to `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute`
5. URL includes query params: rpcids (method ID), source-path, f.sid (session ID), rt=c
6. Body is form-encoded: `f.req=<URL-encoded-JSON>&at=<CSRF-token>&`
7. Response is chunked text with anti-XSSI prefix `)]}'`
8. `decode_response()` strips prefix, parses JSON, extracts RPC result
9. Domain API parses typed response (Notebook, Source, Artifact, etc.)
10. Returns domain object or list to caller

**Chat/Query Flow (Different Endpoint):**

1. `ChatAPI.ask()` builds query with source IDs and conversation context
2. HTTP POST to QUERY_URL (streaming endpoint, not batchexecute)
3. Streaming response with chunked answer text
4. Answer accumulated and returned as single `AskResult`

**Artifact Generation Flow:**

1. `ArtifactsAPI.generate_audio()` calls `CREATE_ARTIFACT` RPC with type code + parameters
2. Returns `GenerationStatus` with task_id (not immediately complete)
3. `wait_for_completion()` polls `LIST_ARTIFACTS` RPC until status changes
4. `download()` fetches URL from artifact metadata or file parameter
5. Saves to disk with progress callback

**State Management:**

- **Auth tokens**: Stored as `AuthTokens` instance in `ClientCore`, updated via `refresh_auth()` callback
- **Conversation cache**: `OrderedDict` in `ClientCore._conversation_cache`, FIFO at 100 items
- **HTTP session**: Single `httpx.AsyncClient` per `ClientCore`, shared across all APIs

## Key Abstractions

**AuthTokens:**
- Purpose: Encapsulates authentication credentials (cookies, CSRF, session ID)
- Examples: `src/notebooklm/auth.py`
- Pattern: Loaded from Playwright storage state, passed to `ClientCore`
- Responsible for: Cookie header generation, token refresh extraction from HTML

**ClientCore:**
- Purpose: Abstracts HTTP + RPC infrastructure from domain APIs
- Examples: `src/notebooklm/_core.py`
- Pattern: Single instance shared by all sub-client APIs (notebooks, sources, etc.)
- Provides: `rpc_call()`, `get_http_client()`, `refresh_auth()` callback support
- Handles: Auth token refresh with shared task coordination to prevent duplicate refreshes

**Domain API Classes:**
- Purpose: Type-safe operations for specific resource domains
- Examples: `NotebooksAPI`, `SourcesAPI`, `ChatAPI`, `ArtifactsAPI` (files: `_notebooks.py`, `_sources.py`, etc.)
- Pattern: Constructor takes `ClientCore`, methods are async, return domain types
- Responsibility: Build RPC params, call core, parse responses into typed objects

**Domain Types:**
- Purpose: Typed representations of API resources
- Examples: `Notebook`, `Source`, `Artifact`, `GenerationStatus`, `ConversationTurn` (file: `types.py`)
- Pattern: Dataclasses with `.from_api_response()` factory method
- Contains: Fields, validation, relationships between resources

**Exception Hierarchy:**
- Purpose: Categorize errors for programmatic handling
- Base: `NotebookLMError` (catch-all)
- Categories: `ValidationError`, `NetworkError`, `RPCError`, `AuthError`, `RateLimitError`, domain-specific (NotebookError, SourceError, ArtifactError, ChatError)
- File: `src/notebooklm/exceptions.py`

**RPC Method Registry:**
- Purpose: Single source of truth for obfuscated method IDs
- Examples: `LIST_NOTEBOOKS = "wXbhsf"`, `CREATE_ARTIFACT = "R7cb6c"`
- File: `src/notebooklm/rpc/types.py` (RPCMethod enum)
- Critical: These change without notice from Google; captured via network traffic analysis

## Entry Points

**Python API:**
- Location: `src/notebooklm/client.py` (`NotebookLMClient` class)
- Triggers: `async with NotebookLMClient.from_storage() as client`
- Responsibilities: Load auth tokens, open HTTP client, expose namespaced APIs, handle lifecycle

**CLI:**
- Location: `src/notebooklm/notebooklm_cli.py` (`cli()` Click group)
- Triggers: `notebooklm <command>`
- Commands registered via `register_session_commands()`, `register_notebook_commands()`, `register_chat_commands()` and `add_command()` for groups
- Global options: `--storage` (auth file path), `-v`/`-vv` (verbosity)

**Main Script:**
- Location: `src/notebooklm/notebooklm_cli.py` (`main()` function)
- Handles: Windows asyncio/encoding quirks before CLI startup

## Error Handling

**Strategy:** Multi-level error detection with automatic retry on auth failures.

**Patterns:**

- **Network Errors (Before RPC):** `NetworkError` for DNS, connection failures, ConnectTimeout
- **RPC Errors (Protocol Level):** `RPCError` base, with specific subclasses:
  - `AuthError`: 401/403 or auth-related RPC error messages
  - `RateLimitError`: HTTP 429 (includes retry-after if available)
  - `ServerError`: HTTP 5xx
  - `ClientError`: HTTP 4xx (not 401/403)
  - `RPCTimeoutError`: Request timeout during RPC
- **Domain Errors:** NotebookError, SourceError, ArtifactError, ChatError for operation-specific failures
- **Auto-Retry on Auth Failure:** `ClientCore.rpc_call()` detects auth errors via `is_auth_error()` predicate, calls `refresh_callback` (which calls `refresh_auth()`), retries once with new tokens
- **Refresh Coordination:** Uses `asyncio.Lock` to ensure only one refresh task runs; concurrent callers await the same task

**Response Handling:**

- `allow_null=False` (default): Raises error if RPC response is null
- `allow_null=True`: Returns null for certain operations (e.g., delete)

## Cross-Cutting Concerns

**Logging:** Configured in `_logging.py`, per-module loggers via `logging.getLogger(__name__)`
- INFO: Major operations (notebook created, source added, etc.)
- DEBUG: RPC details (method name, timing, param count)
- Format: Async-safe, includes timing metrics

**Validation:**
- Input validation at CLI layer (Click option types, callbacks)
- RPC param validation at domain API level (type checking, range checks)
- Response validation in domain type factories (`.from_api_response()`)

**Authentication:**
- CSRF token (SNlM0e) required in request body
- Session ID (FdrFJe) passed in URL query params
- Cookies passed in HTTP headers
- Tokens refresh when RPC detects auth failure (page fetch, regex extraction)
- Retry delay before retrying to avoid immediate failure

**Rate Limiting:**
- Detected via HTTP 429 response
- `RateLimitError` includes optional retry-after seconds
- No automatic retry; client code must handle and backoff

**Timeouts:**
- Granular: connect (10s), read/write (30s, configurable)
- Request timeout (overall): 30s default
- Source processing: Long-poll with 120s timeout
- Artifact generation: Long-poll with variable timeout based on type

---

*Architecture analysis: 2026-03-15*
