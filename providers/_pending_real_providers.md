# Pending Real Providers

SPEC: `01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md` §9 (Pending Providers File)

One real provider now exists in the tree (`real/notegpt/`), and it is
**disabled**. No provider is active for routing.

---

## Status board

| Provider | Type (31 §20) | Status | `is_functional` | Blocking item |
|---|---|---|---|---|
| `notegpt` | C — Session/Cookie Website<br>L — Provider-Native Agent | `disabled` | `false` | Live contract tests + security review (checklist items 9, 10, 14) |

### Why `notegpt` is not active

31 §19.13 — *"Keep provider disabled until tests pass."*

The 101 offline tests in `real/notegpt/tests/` all pass (55 contract, 12
auto-continue bound, 17 attachment-payload wiring, 17 async-boot + login-header).
They cover manifest shape,
capability four-state honesty, error normalization, model catalog, secret
redaction, Core isolation, the auto-continue ceiling, and session
pre-registration. They deliberately do not simulate a successful generation
(31 §11: *"Do not write tests that pretend generation works."*).

Activation therefore still requires:

- [ ] One live `generate_text` round-trip against real credentials.
- [ ] One live `provider_agent` streaming run, confirming the `text` event
      carries the answer (ROUND2 §2 — this event was missing from every
      source document and would silently drop the response).
- [ ] Confirmation of the `164003` → re-login and `164019` → `rotate_identity`
      recovery paths against the live service.
- [ ] Security review of cookie/session handling (checklist item 10).
- [ ] Enable via Admin/Config only after the above (checklist item 14).

---

## Forensic audit remediation (T-V05-001)

Source: `.connect/agents/GSK/FORENSIC_CROSS_REVIEW_NOTEGPT.md`. Fixed items are
listed with the evidence that proves the fix, not merely marked "done".

| ID | Finding | State | Evidence |
|---|---|---|---|
| T-01 | Auto-continue ceiling read a phantom config key `max_continue_attempts`, so the fallback `25` always beat the evidenced `5` (01.06:104); the loop was also entered unconditionally | **fixed** | Ceiling is `limits_mod.should_auto_continue()` only; `sess.continue_calls` has a single increment site. `test_auto_continue.py` (12 tests) |
| T-02 | The loop bound had no behavioural test — the old test only checked the helper, so a 25-request loop passed | **fixed** | Loop driven end-to-end via MockTransport; asserts request count, counter, and `finish_reason` |
| T-03 | `create_chat_session()` hardcoded `"fileInfos": []`, so attachments never reached the provider's history record | **fixed** | `sources` threaded through the chain; `test_file_infos.py` asserts the POSTed body. Reverting to `[]` fails 4 tests |
| T-03b | **Payload confusion, generation side.** `build_stream_payload()` copies its `files` argument verbatim, and the caller passed `request["files"]` raw — so the body shipped **none** of the 5 native stream fields and leaked a foreign `type` key whose `10`/`20` encoding belongs to the *history* shape. Found by the ADDENDUM §1 cross-check; the history side was wired while the stream side was not | **fixed** | Normalized at the single owning call site in `provider_agent.py` via `build_stream_files_payload()`. Observed pre-fix: sent `['name','size','type','url']` vs required `['file_content','file_name','file_size','file_url','mime_type']`. 5 new tests assert the body POSTed to the generation endpoint; reverting fails 4 |
| T-04 | `file_upload` / `vision_input` declared `true` while `upload_asset()` always returns `UNSUPPORTED_CAPABILITY` | **fixed** | Both are now `partial` with named blockers; manifest and code asserted equal by `test_manifest_capabilities_match_code_exactly` |
| T-05 | No test transport existed, so nothing could be tested without live credentials | **fixed** | `tests/mock_transport.py`, exposed as fixtures; not imported by the provider package (Core isolation) |
| T-07 | `except Exception: pass` at `session.py:157` made every pre-registration failure invisible | **fixed** | Now a `logging.warning` with exception type + endpoint + attachment count. Control flow unchanged (still non-fatal). Restoring the silent handler fails 2 tests |
| T-08 | Findings not reflected in documentation | **fixed** | This section |

### Live-runtime round (T-09 / T-10)

Source: live-runtime report from Agent AG (Daytona async sandbox postmortem).
**Evidence class: FIELD observation, not `01.06` script evidence** — these two
defects cannot be re-derived from the reference script, so they are tagged
distinctly from every other row in the table above.

| ID | Finding | State | Evidence |
|---|---|---|---|
| T-09 | **Async sandbox boot invisible.** The Daytona container boots asynchronously (~5-7s); the generation POST only *schedules* it and warm-up frames (`start`, `prepare_env`, `prepare_env_done`) arrive on later `agent-stream/continue` connections. None of those type names were in `KNOWN_EVENTS`, and `iter_events()` ends with an `if etype in KNOWN_EVENTS` filter — measured: **4 warm-up lines in → 0 events out**. No `continue_needed` was produced either, so `while continue_needed:` was never entered: the run ended with zero content *and no error*, indistinguishable from an empty answer | **fixed** | Boot frames surface as the already-known `EVENT_SANDBOX` carrying `boot_pending: True`; a separately-bounded boot-wait phase polls through the window. 17 tests in `test_async_boot.py`. Mutation: reverting the parser kills 6 tests; mapping boot frames to `continue_needed` kills 5 |
| T-10 | **Login was the only un-rotated request.** `auth.login()` hand-rolled its header dict and omitted the IP-rotation trio, so it alone drew app code `164010`. Measured: `build_headers()` = 10 keys incl. `client-ip`/`x-forwarded-for`/`x-real-ip`; `login()` = 5 keys, all three missing | **fixed** | `login()` now derives from `build_headers()` (single definition of the rotation set, so the paths cannot drift), layering only its own `content-type` + `/login` referer. Mutation: restoring the hand-rolled dict kills 3 tests |

**Two shortcuts from the reference fix were deliberately NOT adopted:**

1. **Raising `auto_continue_limit` to 20.** That silently repeals the
   script-evidenced ceiling of 5 (01.06:104) which T-01 was opened to restore,
   and makes container warm-up spend the *truncation* budget — a slow boot would
   then abort a perfectly healthy answer. Boot waiting instead has its own
   `BOOT_POLL_LIMIT = 12`, and boot polls do **not** touch
   `sess.continue_calls`. Guarded by `test_boot_polling_does_not_consume_the_truncation_budget`
   and `test_boot_bound_is_independent_of_the_truncation_ceiling`; mutation
   (limit → 20 + unified bound) kills **7** tests.
2. **Persisting the session token to `active_token.txt`.** A plaintext
   credential written next to the source, in a repo whose `.gitignore` has **no**
   token/secret pattern — one `git add -A` commits a live session token.
   This directly contradicts onboarding item 5 (env-only credentials, currently
   *done* and test-guarded). **Rejected; not implemented.** If login
   rate-limiting needs mitigation beyond IP rotation, it must use the existing
   env-var path or an explicitly reviewed secret store.

### Still open — NOT fixed by T-V05-001

- **Upload path (the root blocker).** The official `POST /api/v1/upload/sign-url`
  path needs an HMAC `sign` field with an undocumented derivation
  (CORRECTIONS.md §5). It cannot be implemented by guessing, and the only
  working alternative transits `tmpfiles.org`, a public third-party host
  (ROUND2 §3). This single blocker is why `file_upload` and `vision_input` are
  `partial` rather than `true`. **Requires upstream reverse-engineering or a
  vendor answer — not a code change.**
- **Broken CDN fallback** at 01.06:174 embeds a hardcoded date `2026/08/25`,
  making the fallback URL structurally dead on any other day. The reference
  script is outside the provider package and was deliberately not modified.
- **`build_stream_payload()` still trusts its caller.** The T-03b fix normalizes
  attachments at the call site because `runtime/request.py` is outside the
  agreed whitelist for this round. The builder therefore still copies any
  `files` argument verbatim, so a *future* caller could reintroduce the same
  confusion. The durable fix is to normalize inside the builder (or reject a
  non-native shape); the tests added here would catch a regression on the
  existing path, but not a brand-new caller. **Deferred, needs scope approval.**
- **Live verification** of every path above (see the activation list) still
  requires real credentials; all 101 tests are offline by design.
- **T-09/T-10 rest on second-hand field evidence.** Both were reproduced and
  fixed against the *reported* wire behaviour, not against a live service this
  agent observed. The reported boot window (5-7s) and frame names are taken on
  trust; `BOOT_POLL_LIMIT = 12` is a ~2x margin over that unverified figure.
  A live run must confirm the frame names and the timing. **Unverified upstream
  input — do not treat the numbers as evidenced.**
- **The reported CLI timing (6.8s) was not reproduced here** and is not claimed:
  it depends on live credentials this agent does not have.

---

## Onboarding checklist state (31 §19)

| # | Item | State |
|---|---|---|
| 1 | Identify provider type and auth method | done — session/cookie, no OAuth, no Clerk |
| 2 | Document real capabilities | done — four-state, evidence-tagged; `file_upload`/`vision_input` corrected `true` → `partial` with named blockers |
| 3 | Create real manifest | done — `manifest.yaml`, `is_template: false` |
| 4 | Implement only declared operations | done — 6 undeclared ops return `UNSUPPORTED_CAPABILITY` |
| 5 | Credential handling without plaintext secrets | done — env-only, `redacted()`, guarded by test |
| 6 | Implement health check | done — reports `SUSPENDED` while disabled |
| 7 | Implement error normalization | done — 12 spec categories, app-code precedence over HTTP 200 |
| 8 | Rate/limit behavior if known | partial — fabricated numbers reported as `unknown`; only `AUTO_CONTINUE_LIMIT=5` is evidenced |
| 9 | Contract tests per declared capability | **pending live** — offline tests done (101 pass); auto-continue bound, both attachment payload shapes, async sandbox boot + login header rotation now covered |
| 10 | Security checks for secrets and tenant isolation | **pending review** |
| 11 | Register provider in Provider Registry | **pending** — no registry module exists in this repo yet |
| 12 | Register model/provider bindings | done in-provider — 36 models, 7 phantoms excluded |
| 13 | Keep provider disabled until tests pass | enforced — activation gate raises `ProviderDisabledError` |
| 14 | Enable via Admin/Config after verification | **not done — intentionally** |

---

## Required before adding any further provider

- Choose provider type.
- Real provider API/auth details
- Capability discovery / document capabilities
- Model list or discovery method
- Define operations
- Credential handling
- Rate limit behavior
- Error mapping
- Health checks
- Contract tests
- Security review

## Candidate provider categories

Coverage below refers to the 12 categories in 31 §6. `notegpt` contributes
only where the evidence supports it — the remaining rows are open, and must
not be filled by declaring capabilities the provider does not have.

- [x] Provider-native agent — `notegpt` (CONFIRMED)
- [x] Chat/Text (API key text/chat) — `notegpt` covers chat via session auth, not API key
- [x] Reasoning — `notegpt` (2 evidenced reasoning models)
- [ ] Coding
- [ ] OAuth provider
- [x] Session/cookie website provider — `notegpt`
- [ ] Vision (input) — `notegpt` declares `partial`: the `image_recognition`
      tool is real (01.05:1076) but its input depends on the blocked upload
      path, so the capability cannot complete
- [ ] Image generation — `notegpt` declares `unknown`
- [ ] Audio STT
- [ ] Audio TTS
- [ ] Embeddings
- [ ] Rerank
- [ ] Moderation
- [ ] Multimodal

## Not applicable for `notegpt`

Per 31 §12 (*"Scaffold Must Not Force One Provider Shape"*), these are
recorded as not-applicable rather than as pending work:

- Account pool / lease / cooldown — `account_pool.supported: false`
  (CORRECTIONS.md §7: the documented pool never existed; the real recovery
  path is `rotate_identity()` on a single account).
- Account registration, update, delete — no such endpoints.
- Agent run/thread handles — `conversation_id` is the only state handle.
