# T-NGPT-001 — Pre-mutation audit

Date: 2026-08-26
Agent: AR

## Sources read

1. `01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md` — architecture and
   contracts are authoritative.
2. `projects/ngpt/scripts/01.06_notegpt_agent_mode.py` — request order,
   payloads, authentication, SSE handling, identity rotation, and CLI behavior.
3. Gist `6c5110b4e0adf0756a91d20c4485771b` — previous live-runtime failure
   report and the requested surgical repair plan.
4. Current `providers/real/notegpt/` implementation and its tests.

## Contracts that must remain unchanged

- The adapter public surface remains `NoteGPTProvider` + `get_provider`.
- `stream_agent_run(config, request) -> Generator` and
  `run_provider_agent(config, request) -> Dict` signatures remain unchanged.
- Provider internals remain behind `providers/real/notegpt/`; Core-facing code
  does not import runtime/operation internals.
- The provider remains `status: disabled` / `is_functional: false`.
- The existing normalized error categories and attachment payload shapes remain
  unchanged.
- No live tests or credentials are added.

## Actual deviations found before mutation

### D1 — Continue response is not fully drained by the caller

`_continue_stream()` yields all parsed events, but the outer auto-continue loop
breaks as soon as it sees `EVENT_CONTINUE_NEEDED`. If the same HTTP response has
more events after that marker, those events are lost. The reference loop keeps
consuming the response body; the Gist explicitly calls this a premature stream
drain. The fix must record the marker and continue iterating, not break.

### D2 — Continue requests reuse a stale request context

`ctx` is created once before the first generation request and passed to every
`_continue_stream()` call. The reference `_build_headers()` is called for every
continue request, generating a fresh IP and carrying the current active token.
The repair must rebuild the auth context immediately before each continue POST,
while preserving the same `conversation_id` and session cookie identities.

### D3 — Recovery rotates IDs but does not refresh the active session

On a recoverable app code, current `stream_agent_run()` calls
`ConversationSession.rotate_identity()` and rebuilds a context, but does not
invoke `auth.refresh_session()`/`auth.login()` or refresh the transport cookie
jar. The reference `rotate_identity()` invokes `login_and_refresh_token()`, then
rebuilds its cookies and scraper. The repair will preserve provider state and
conversation ID while refreshing authentication through the runtime boundary.

### D4 — `nc_token` from the reference login flow is not carried

The reference login copies `scraper.cookies["nc_token"]` (falling back to the
new token) into its request cookies. Current `build_cookies()` only carries
`anonymous_user_id`, `sbox-guid`, and `user_token`. The runtime cookie builder
must include the observed companion cookie without exposing its value in logs.

### D5 — Session pre-registration is yielded after the user-facing sandbox event

The reference calls `_create_chat_session()` before yielding the initial sandbox
status and before the generation POST. Current code yields first, then performs
pre-registration when the generator is advanced. The network order is still
ultimately serial, but the observable generator/request sequence is not
reference-compatible. Move only the status yield below pre-registration; do not
change the pre-registration payload or its non-fatal semantics.

### D6 — CLI progress events can corrupt streamed output

Current `__main__.py` prints every `sandbox` and `info` event regardless of the
current phase. The Gist requires setup/continue status output to be limited to
`phase == "init"`, so it cannot interleave with reasoning/final text. Prompt-file
fallback already exists and must remain intact.

### D7 — Baseline repository hygiene gate is red

The existing suite is `137 passed, 1 failed` because tracked `.pytest_cache/*`
files match the repository's own `.gitignore`. This is not a provider behavior
change, but it blocks the required verification gate and must be removed from
Git tracking without changing product code.

## Follow-up live-evidence audit (before T-NGPT-002 mutation)

The pasted execution report is consistent with a real parser gap, not proof that
144 mock tests cover the wire. The reference handles these raw event types in
`01.06:872-874`:

- `create_sandbox`
- `resume_sandbox`

The current parser only recognized `start`, `prepare_env`, and
`prepare_env_done`. A direct offline probe before the follow-up fix showed:

```text
create_sandbox -> []
resume_sandbox -> []
prepare_env    -> EVENT_SANDBOX(boot_pending=True)
```

Therefore a live `create_sandbox`/`resume_sandbox` frame was dropped, leaving
`boot_pending` false and allowing the terminal `empty_stream` path. The
follow-up scope is limited to mapping the two reference event names and their
`data.message` step field into the existing known `EVENT_SANDBOX` contract, plus
keeping a scheduling `[DONE]` sentinel from becoming a terminal event before
that bounded wait. The existing bounded boot wait remains unchanged.

## Non-deviations deliberately left alone

- `status: disabled` and `is_functional: false` remain locked.
- The spec-required normalized provider interface and error categories are not
  renamed or replaced.
- The `AUTO_CONTINUE_LIMIT = 5` truncation ceiling is not raised; it is separate
  from the bounded async-boot wait.
- No endpoint, model, credential, or rate-limit value is invented.
- The existing reference-vs-corrections success-code evidence is not broadened
  in this task; no unrelated error taxonomy refactor is performed.
