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

The 44 contract tests in `real/notegpt/tests/test_contract.py` all pass, but
they are **offline** tests: manifest shape, capability tri-state, error
normalization, model catalog, secret redaction, Core isolation. They
deliberately do not simulate a successful generation (31 §11: *"Do not write
tests that pretend generation works."*).

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

## Onboarding checklist state (31 §19)

| # | Item | State |
|---|---|---|
| 1 | Identify provider type and auth method | done — session/cookie, no OAuth, no Clerk |
| 2 | Document real capabilities | done — tri-state, evidence-tagged |
| 3 | Create real manifest | done — `manifest.yaml`, `is_template: false` |
| 4 | Implement only declared operations | done — 6 undeclared ops return `UNSUPPORTED_CAPABILITY` |
| 5 | Credential handling without plaintext secrets | done — env-only, `redacted()`, guarded by test |
| 6 | Implement health check | done — reports `SUSPENDED` while disabled |
| 7 | Implement error normalization | done — 12 spec categories, app-code precedence over HTTP 200 |
| 8 | Rate/limit behavior if known | partial — fabricated numbers reported as `unknown`; only `AUTO_CONTINUE_LIMIT=5` is evidenced |
| 9 | Contract tests per declared capability | **pending live** — offline contract tests done |
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
- [ ] Vision (input) — `notegpt` declares `unknown`, not supported
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
