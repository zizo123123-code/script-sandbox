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

The 79 offline tests in `real/notegpt/tests/` all pass (55 contract, 12
auto-continue bound, 12 `fileInfos` wiring). They cover manifest shape,
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
| T-03 | `create_chat_session()` hardcoded `"fileInfos": []`, so attachments never reached the provider's history record | **fixed** | `sources` threaded through the chain; `test_file_infos.py` (12 tests) asserts the POSTed body. Reverting to `[]` fails 4 tests |
| T-04 | `file_upload` / `vision_input` declared `true` while `upload_asset()` always returns `UNSUPPORTED_CAPABILITY` | **fixed** | Both are now `partial` with named blockers; manifest and code asserted equal by `test_manifest_capabilities_match_code_exactly` |
| T-05 | No test transport existed, so nothing could be tested without live credentials | **fixed** | `tests/mock_transport.py`, exposed as fixtures; not imported by the provider package (Core isolation) |
| T-07 | `except Exception: pass` at `session.py:157` made every pre-registration failure invisible | **fixed** | Now a `logging.warning` with exception type + endpoint + attachment count. Control flow unchanged (still non-fatal). Restoring the silent handler fails 2 tests |
| T-08 | Findings not reflected in documentation | **fixed** | This section |

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
- **Live verification** of every path above (see the activation list) still
  requires real credentials; all 79 tests are offline by design.

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
| 9 | Contract tests per declared capability | **pending live** — offline tests done (79 pass); auto-continue bound + `fileInfos` chain now covered |
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
