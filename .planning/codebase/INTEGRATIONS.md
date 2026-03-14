# External Integrations

**Analysis Date:** 2026-03-15

## APIs & External Services

**Google NotebookLM (Primary):**
- Service: Google NotebookLM - Unofficial RPC-based client
  - SDK/Client: Internal (reverse-engineered batchexecute protocol)
  - Auth: Cookie-based (from Playwright storage_state.json)
  - Implementation: `src/notebooklm/rpc/` (encoder, decoder, types)

**RPC Endpoints:**
- Batchexecute API - General operations
  - Endpoint: `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute`
  - Used for: Notebooks, sources, artifacts, notes, mind maps, sharing, chat turns
  - Client: `src/notebooklm/_core.py` (ClientCore.rpc_call)
  - Obfuscated method IDs in `src/notebooklm/rpc/types.py` (RPCMethod enum)
  - Methods: wXbhsf (list notebooks), CCqFvf (create), rLM1Ne (get), izAoDd (add source), R7cb6c (create artifact), etc.
  - Auth: CSRF token (SNlM0e) + session ID (FdrFJe) + cookies

- Streaming Query API - Chat/Ask operations
  - Endpoint: `https://notebooklm.google.com/_/LabsTailwindUi/data/google.internal.labs.tailwind.orchestration.v1.LabsTailwindOrchestrationService/GenerateFreeFormStreamed`
  - Used for: Question answering with reference extraction
  - Client: `src/notebooklm/_chat.py` (ChatAPI.ask)
  - Auth: Same as batchexecute (CSRF + session + cookies)
  - Response parsing: `_parse_ask_response_with_references` method

- Upload API - File uploads
  - Endpoint: `https://notebooklm.google.com/upload/_/`
  - Used for: Adding file sources to notebooks
  - Not directly called; registered via batchexecute RPC after upload

## Data Storage

**Databases:**
- None - Fully stateless library
- No persistent state except local caching of conversation turns

**File Storage:**
- Local filesystem only - No cloud storage integrations
  - Playwright storage_state.json: `~/.notebooklm/storage_state.json` (contains Google auth cookies)
  - Browser profile: `~/.notebooklm/browser-profile/` (persistent browser data for login)
  - Context file: `~/.notebooklm/context.json` (current notebook ID and metadata)
  - Language config: `~/.notebooklm/language.json` (user's output language preference)
- Custom path support via NOTEBOOKLM_HOME environment variable
- All file operations path-traversal protected

**Caching:**
- In-memory conversation cache (OrderedDict) - See `src/notebooklm/_core.py`
  - MAX_CONVERSATION_CACHE_SIZE = 100 conversations
  - FIFO eviction when limit exceeded
  - Caches Q&A turns for conversation continuity within a session
  - See `cache_conversation_turn()` and `get_cached_conversation()`

## Authentication & Identity

**Auth Provider:**
- Custom - Google cookie-based authentication
  - Implementation: `src/notebooklm/auth.py`
  - Mechanism: Playwright browser automation captures Google auth cookies during login
  - Cookie extraction: `extract_cookies_from_storage()` from storage_state.json
  - Regional support: Handles regional Google domains (.google.com.sg, .google.co.uk, .google.de, etc.)
  - See `GOOGLE_REGIONAL_CCTLDS` constant for 100+ supported regional domains

**Token Management:**
- CSRF Token (SNlM0e) - Required for all RPC calls
  - Extracted from NotebookLM HTML: `extract_csrf_from_html()`
  - Fetched via `fetch_tokens()` after cookie loading
  - Attached to request body in `build_request_body()` (encoded as "at" parameter)

- Session ID (FdrFJe) - Unique per-session identifier
  - Extracted from NotebookLM HTML: `extract_session_id_from_html()`
  - Passed in URL query parameters (f.sid)
  - Updated on auth refresh

**Token Refresh:**
- Automatic on auth failure (401/403 or auth-related error)
  - See `is_auth_error()` in `src/notebooklm/_core.py`
  - Triggered by `AuthError`, HTTP 401/403, timeout, or auth-related messages
  - Retry mechanism in `_try_refresh_and_retry()` with shared task coordination
  - Max one retry per call (prevents infinite loops)

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service

**Logs:**
- Python logging module (standard library)
  - Configuration: `src/notebooklm/_logging.py`
  - Log levels: DEBUG (detailed RPC info), INFO (major actions), WARNING (retries, missing features), ERROR (failures)
  - Logger names: Hierarchical under `notebooklm` namespace
  - Key loggers:
    - `notebooklm._core`: RPC call timing and auth retries
    - `notebooklm.auth`: Cookie extraction and token fetch
    - `notebooklm.cli`: Command execution tracing
    - `notebooklm.rpc`: Request encoding/decoding

## CI/CD & Deployment

**Hosting:**
- Not applicable - Library only (no deployed service)
- PyPI distribution: Package published to PyPI as `notebooklm-py`

**CI Pipeline:**
- GitHub Actions (inferred from repo structure)
  - Test markers: `@pytest.mark.e2e` for end-to-end tests (require auth)
  - Coverage requirement: 90% minimum (via pytest-cov config)
  - Timeout: 60 seconds global (pytest-timeout)

**Distribution:**
- PyPI (Python Package Index)
  - Entry point: `notebooklm` CLI command via `notebooklm.notebooklm_cli:main`
  - Build: hatchling with README hook for version-tagged docs

## Environment Configuration

**Required env vars:**
- NOTEBOOKLM_AUTH_JSON (optional but recommended for CI/CD)
  - Format: Playwright storage_state JSON with cookies
  - Use in pipelines to avoid file writes
  - If missing, falls back to file-based: ~/.notebooklm/storage_state.json

**Optional env vars:**
- NOTEBOOKLM_HOME - Custom config directory
- NOTEBOOKLM_VCR_RECORD - Enable VCR cassette recording (test development)
- NOTEBOOKLM_BL - Override browser loader version (advanced)

**Secrets location:**
- storage_state.json: Contains sensitive Google auth cookies
  - File permissions: 0o600 (owner-read/write only)
  - See `context.storage_state()` in session.py and chmod protection

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None - Fully synchronous request-response only

**Async Patterns:**
- All API operations are async-first
- Request counter for chat API: `_reqid_counter` in ClientCore (increments by 100k per call)
- Conversation history passed with each chat request for continuity

---

*Integration audit: 2026-03-15*
