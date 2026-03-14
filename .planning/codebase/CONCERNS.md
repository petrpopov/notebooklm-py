# Concerns

## Critical Issues

### RPC Method ID Brittleness
**Severity**: Critical | **Files**: `src/notebooklm/rpc/types.py`

All RPC method IDs are undocumented Google internal identifiers. Google can change them without notice, breaking the entire library. The project has a GitHub Actions workflow (`rpc-health.yml`) and `scripts/check_rpc_health.py` for monitoring, but there's no automated recovery — manual updates required.

**Impact**: Any Google infrastructure change can silently break all functionality.

### Deeply Nested RPC Parameter Structures
**Severity**: High | **Files**: `src/notebooklm/rpc/encoder.py`, `src/notebooklm/_sources.py`

RPC params are position-sensitive nested lists. Source IDs require different nesting depending on operation: `[id]`, `[[id]]`, `[[[id]]]`, or `[[[[id]]]]`. This is brittle and undocumented — any mistake causes silent failures or cryptic errors.

**Impact**: Easy to introduce bugs when adding new RPC operations.

---

## Tech Debt

### Large _artifacts.py File
**Files**: `src/notebooklm/_artifacts.py` (~2325 lines per agent analysis)

Artifact parsing requires multiple helper functions and the file has grown large. Complex nested response parsing with fallback logic makes it hard to maintain.

### Null/None Return Values
**Files**: Multiple `_*.py` files

Several API methods return `None` on partial success or when rate-limited instead of raising exceptions. This makes error handling inconsistent for callers.

### Missing Rate Limit Handling
**Files**: `src/notebooklm/_core.py`

No built-in exponential backoff or rate limit retry logic. Callers must add their own delays. Bulk operations fail silently under load. Documented in CLAUDE.md as a known pitfall.

### Conversation Cache Without Bounds
**Files**: `src/notebooklm/_chat.py`

Chat conversation history is cached in-memory without size limits or TTL. Long-running sessions could accumulate unbounded memory.

---

## Security Considerations

### Session Cookies Stored in Plaintext
**Files**: `src/notebooklm/paths.py`, `src/notebooklm/auth.py`

Auth tokens (session cookies, CSRF tokens) stored in `~/.notebooklm/` as plaintext files. No encryption at rest. Documented in `SECURITY.md`.

### Browser-Based Authentication Window
**Files**: `src/notebooklm/auth.py`

Playwright launches a visible browser window for login. The auth flow captures cookies from the browser session. This is the only supported auth method — no API keys or OAuth.

### RPC Method IDs as Fingerprint
The reverse-engineered RPC endpoint structure is visible in traffic analysis, potentially exposing the library to Google's detection/blocking.

---

## Performance Concerns

### Synchronous File Upload Path
**Files**: `src/notebooklm/_sources.py`

File uploads use httpx but may block the event loop for large files. No streaming/chunked upload support documented.

### No Streaming for Large Responses
**Files**: `src/notebooklm/_core.py`

All responses are loaded fully into memory. Large artifact downloads (videos, audio) are fully buffered before writing to disk.

### Artifact Download URL Expiry
**Files**: `src/notebooklm/_artifacts.py`

Download URLs returned by artifact generation have short TTLs. If download is delayed after generation, URLs expire and the operation must be retried from scratch.

---

## Fragile Areas

### RPC Response Decoder
**Files**: `src/notebooklm/rpc/decoder.py`

Parsing relies on positional index navigation through nested lists and regex pattern matching. Response structure changes from Google would break parsing silently (returning `None` rather than raising exceptions in many places).

### Source Type Detection
**Files**: `src/notebooklm/_sources.py`, `src/notebooklm/_url_utils.py`

YouTube URL detection uses regex patterns. Other source type detection is heuristic. Edge cases (unusual URL formats, non-standard file types) may be misclassified.

### Authentication Token Refresh
**Files**: `src/notebooklm/auth.py`, `src/notebooklm/_core.py`

CSRF tokens expire. The auto-refresh logic may have race conditions under concurrent use. Documented in CLAUDE.md as a known pitfall.

### Chat API Response Structure
**Files**: `src/notebooklm/_chat.py`

Chat API returns inconsistent tuple structures depending on response type. Multiple parse paths create fragile conditional logic.

---

## Missing Features

### No Progress Feedback for Long Operations
Artifact generation (podcasts, videos) can take minutes with no progress updates. Users must poll or wait blindly.

### No Windows-Compatible Path Handling
Some path operations may have edge cases on Windows (noted in `tests/unit/test_windows_compatibility.py` — these tests exist but coverage may be incomplete).

### No Streaming Support for Real-Time Chat
Chat responses are returned as complete messages, not streamed token-by-token.

---

## Test Coverage Gaps

### RPC Encoder/Decoder Edge Cases
Deeply nested parameter structures for rare operations may lack test coverage. Integration tests rely on cassettes that may not cover all error paths.

### Authentication Refresh Under Concurrency
No tests for concurrent requests triggering simultaneous token refresh.

### Real API Response Fixtures
Artifact parsing tests may use synthetic fixtures that don't match all real API response variations.

---

## Dependencies at Risk

| Dependency | Risk |
|-----------|------|
| Playwright | Version pinning issues on Linux (documented in troubleshooting); heavy browser dependency for auth only |
| vcrpy | Cassette format compatibility between versions |
| httpx | Core dependency; major version bumps could break internals |
| Google NotebookLM API | Any Google-side change breaks everything (fundamental risk) |

---

## Monitoring

- **RPC Health Check**: `.github/workflows/rpc-health.yml` runs nightly
- **Nightly E2E**: `.github/workflows/nightly.yml` tests real API flows
- **Script**: `scripts/check_rpc_health.py` for manual RPC verification
- **Diagnose**: `scripts/diagnose_get_notebook.py` for debugging notebook fetch failures
