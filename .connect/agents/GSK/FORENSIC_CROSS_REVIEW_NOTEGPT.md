# FORENSIC CROSS-REVIEW — NoteGPT Provider

> **Protocol**: Gist `4c20bbd9a9597a6515711b17c87f41c0` — MASTER INDEPENDENT
> FORENSIC CROSS-REVIEW. Boundary §20 = **AUDIT ONLY**. No code was modified
> while producing this report.
> **Date**: 2026-08-26 · **Agent**: GSK · **Commit**: `3643f9f`

---

## 1. Executive Verdict

```text
ARCHITECTURE:        PASS
BEHAVIORAL PARITY:   PARTIAL
TEST COVERAGE:       PARTIAL
STATE ISOLATION:     PARTIAL
REFERENCE READINESS: NOT READY
```

**Answer to the gist's FINAL QUESTION** — `providers/real/notegpt/` is:

> **A Functional Provider with confirmed behavioral-parity gaps.**
> It is **NOT** a bare scaffold (real HTTP I/O, real SSE parsing, real
> auto-continue exist), and it is **NOT** yet a Reference Implementation
> (three P0/P1 parity defects below, plus untested runtime paths).

Anti-anchoring note: the previous session's summary ("48/48 passing, all clean")
is `PARTIALLY_CONFIRMED`. The tests do pass, but they are **contract-only** and
do not touch the code paths where the defects live — so "clean" overstated the
evidence. See §7.

---

## 2. Method & Sources Actually Read

| Layer | Source | Status |
|---|---|---|
| Architecture | `01_30_...SPEC.md`, `01_31_...ONBOARDING.md`, `01.01/01.02_DATABASE_REFERENCE.md` | read |
| Legacy | `projects/ngpt/scripts/01.06_notegpt_agent_mode.py` (1334 LOC) | read |
| Legacy (prior) | `01.02`–`01.05` in `scripts/`, 6 archive copies | cross-checked |
| Inventory | `inventory/notegpt/` (13 files incl. `CORRECTIONS*.md`) | read |
| Current | `providers/real/notegpt/` (50 files, 4606 LOC) | read |
| Tests | `tests/test_contract.py` (483 LOC, 48 tests) | executed + read |

---

## 3. Architecture Matrix

| Requirement | Current | Evidence | Gap | Sev |
|---|---|---|---|---|
| Core sees no transport detail (30 §9) | PASS | headers/cookies/TLS confined to `runtime/request.py` | — | — |
| Provider exports adapter only (31 §7) | PASS | `__init__.py` exports 2 names; asserted by test | — | — |
| No Core imports from provider | PASS | grep: zero `from core` / `import core` | — | — |
| Tri-state capabilities | PASS | `CONFIRMED` / `UNKNOWN` / rejected split | — | — |
| Error normalization at boundary | PASS | `errors.py` 307 LOC, app-code-wins | — | — |
| `status: disabled` until verified | PASS | manifest + guard test | — | — |
| Endpoint fidelity | PASS | 11 endpoints identical to legacy, HAR-counted | — | — |
| Secret hygiene | PASS | env-only, `__repr__` redaction, no literals | — | — |

Architecture compliance is genuinely strong. The defects are **behavioral**, not structural.

---

## 4. Legacy Parity Matrix

| Legacy behavior (01.06) | Current | Verdict | Sev |
|---|---|---|---|
| 11 endpoints | identical | `BEHAVIORALLY EQUIVALENT` | — |
| Header set `:552-566` (3 IP headers, same value) | verbatim | `BEHAVIORALLY EQUIVALENT` | — |
| `generate_fake_ip()` `:386` | ported | `BEHAVIORALLY EQUIVALENT` | — |
| Anonymous fallback on login 164010 `:519` | ported | `BEHAVIORALLY EQUIVALENT` | — |
| SSE 13 events + alias | ported | `BEHAVIORALLY EQUIVALENT` | — |
| Auto-continue loop `:890-908` | present but **two conflicting ceilings** | `BEHAVIORAL DIFFERENCE` → **regression** | **P0** |
| `fileInfos` in session pre-register `:620` | **hardcoded `[]`** | `BEHAVIORAL DIFFERENCE` → **missing behavior** | **P1** |
| `files[]` native payload `:759` | assembled, but no source can reach it | `PARTIALLY_SUPPORTED` | **P1** |
| `tmpfiles.org` transit `:166` | documented, not wired | intentional migration | P2 |
| `scan_attachments_folder()` `:177` | **absent** | missing (CLI-only concern) | P2 |
| `active_session.txt` persistence | **absent** | `BEHAVIORAL DIFFERENCE` | P2 |

---

## 5. Confirmed Gaps

### GAP-01 — Two contradictory auto-continue ceilings `P0`

```text
FINDING:   Auto-continue budget is enforced by two different limits.
STATUS:    CONFIRMED
SOURCE:    01.06:104  AUTO_CONTINUE_LIMIT = 5
FILE:      operations/provider_agent.py:207  (outer loop)
           discovery/limits.py:109-111       (inner guard)
OBSERVED:  outer  `max_attempts = getattr(config, "max_continue_attempts", 25)`
           — `max_continue_attempts` is defined NOWHERE in the package, so
           getattr always falls back to 25.
           inner  `should_auto_continue()` correctly stops at 5.
EXPECTED:  a single ceiling of 5, per the only evidenced limit.
IMPACT:    The outer loop can issue up to 25 POSTs to agent-stream/continue.
           The inner guard only fires on a `continue_needed` event; when the
           stream ends WITHOUT that event, `done_received` stays False and the
           outer loop re-enters — each iteration with `time.sleep(1)`.
           Worst case: 25 network rounds where legacy allowed 5 → 5x quota burn
           against a provider whose quota exhaustion (164019) triggers identity
           rotation. Also silently sets `recovery_used = True` on every pass.
SEVERITY:  P0
CONFIDENCE: HIGH
```
Note the dead config key is the actual root cause — this reads like an intended
override that was never added to `NoteGPTConfig`.

### GAP-02 — `fileInfos` hardcoded to `[]` `P1`

```text
FINDING:   Session pre-registration always sends an empty attachment array.
STATUS:    CONFIRMED
SOURCE:    01.06:580-594 _build_file_infos_for_history() → :620 "fileInfos": file_infos
FILE:      runtime/session.py:149
OBSERVED:  "fileInfos": [],   ← literal, no parameter, no caller can populate it
           `create_chat_session()` has no `sources` argument at all, whereas the
           legacy `_create_chat_session(prompt, sources)` accepted one.
EXPECTED:  the 7-field records {type,url_type,url,title,size,origin_url,
           transcriptUrl} that legacy built (type 10=image, 20=document).
IMPACT:    Attachments never appear in provider-side conversation history.
           Any provider feature keyed off history attachments degrades.
NOTE:      assets/upload.py:152 build_native_files_payload() produces EXACTLY
           this 7-field shape — the builder exists and is simply never called
           from session.py. This is a wiring gap, not a missing capability.
SEVERITY:  P1
CONFIDENCE: HIGH
```

### GAP-03 — `file_upload: true` is unreachable end-to-end `P1`

```text
FINDING:   Manifest advertises file_upload as CONFIRMED, but no code path can
           turn a local file into a hosted URL.
STATUS:    CONFIRMED
FILE:      manifest.yaml:85 · discovery/capabilities.py:37 (CONFIRMED dict)
           vs assets/upload.py:126 (Path A = STUB, HMAC `sign` unknown)
              assets/upload.py:55  (Path B tmpfiles.org — constant only, no call)
OBSERVED:  Path A returns UNSUPPORTED_CAPABILITY; Path B is never invoked.
           Only `build_native_files_payload()` works, and it REQUIRES a URL
           that already exists.
EXPECTED:  either a working path, or capability demoted to PARTIALLY_SUPPORTED.
IMPACT:    Chain `Input → Upload → Remote Ref → Payload` is broken at step 2.
           `vision_input: true` inherits the same break (vision_analysis.py:42
           forwards `files`/`images` it cannot itself produce).
SEVERITY:  P1  (documentation/manifest honesty defect, per gist §15 + §17)
CONFIDENCE: HIGH
```

---

## 6. Contradictions (gist §17)

| Axis | Contradiction |
|---|---|
| Tests ↔ Code | `test_auto_continue_limit_is_five` asserts 5 and passes, yet the shipping path allows 25. The test validates the *helper*, never the *loop* → false assurance. |
| Manifest ↔ Implementation | `file_upload: true` / `vision_input: true` vs a stubbed uploader (GAP-03). |
| Legacy ↔ Current | `fileInfos` populated vs hardcoded `[]` (GAP-02). |
| Config ↔ Code | `max_continue_attempts` read via getattr but never defined. |
| Docs ↔ Code | `providers/README.md` + `_pending_real_providers.md` list only "live tests + security review" as blockers; the three gaps above are undocumented. |

---

## 7. Previous-Agent Claims

| Claim | Evidence | Verdict |
|---|---|---|
| "48/48 tests pass" | reproduced, 0.24s | `CONFIRMED` |
| "Structure matches §6.2" | 50 files, all modules present | `CONFIRMED` |
| "No secrets / no Core imports / no bare except" | grep clean | `CONFIRMED` |
| "All checks clean" | tests never exercise the defective loop | `REFUTED` |
| "Only blockers are live tests + security review" | GAP-01/02/03 are code defects | `REFUTED` |
| "Pool = NOT_APPLICABLE" | 7 files, docstring-only, `supported=false` | `CONFIRMED` |
| Provider is "reference ready" | three parity defects | `REFUTED` |

**Anchoring bias detected**: prior reporting used *test count* and *file count*
as quality proxies — exactly the trap gist §13 warns about.

---

## 8. Missing Tests

| Area | Status | Why it matters |
|---|---|---|
| Auto-continue **loop** bound | `UNTESTED` | would have caught GAP-01 |
| `create_chat_session` payload shape | `UNTESTED` | would have caught GAP-02 |
| Attachment flow end-to-end | `UNTESTED` | would have caught GAP-03 |
| `ConversationSession` isolation / concurrency | `UNTESTED` | no test constructs two sessions |
| `_open_stream` / network failure | `UNTESTED` | no mock transport exists |
| `_continue_stream` recursion depth | `UNTESTED` | recursive; unbounded-depth risk |
| Error mapping, manifest, catalog, secrets | `TESTED` | 48 tests concentrate here |

Root cause: there is **no fake/mock transport layer**, so every test is a pure
data assertion. That is the single highest-leverage structural fix.

---

## 9. Stub Audit

| Stub | Arch | Legacy | Verdict |
|---|---|---|---|
| `pool/*` (7 files) | optional | absent | **legitimate** — `supported=false`, documented |
| `audio_stt/tts`, `embeddings`, `rerank`, `moderation` | optional | absent | **legitimate** — `CONFIRMED_UNSUPPORTED` |
| `image_generation` | optional | absent | **legitimate** — declared `UNKNOWN` |
| `account/create·delete·update` | optional | partial | **legitimate** — blocker documented |
| `assets/upload` Path A | required by manifest | present | **misleading** — capability says `true` (GAP-03) |
| `vision_analysis` | required by manifest | present | **misleading** — depends on broken upload |

---

## 10. State Isolation

`ConversationSession` is a dataclass with no shared mutable default and no
global registry — no cross-tenant contamination found. But:

- `sess.continue_calls` is mutated in **two places** (`provider_agent.py:210`
  assigns, `:256` increments) → the counter is not a single source of truth.
- No ownership field (tenant/user) on the session object.
- `active_session.txt` persistence from legacy is simply absent; no replacement
  documented.
- `_continue_stream` recurses without a depth cap.

Verdict: `PARTIAL` — safe by construction today, unverified under concurrency.

---

## 11. Security Notes (gist §1 — test creds are NOT findings)

`projects/ngpt/active_session.txt` and dev credentials are treated as
Dev/Test data per §1 and are **not** reported as defects. Real design issues:

1. `runtime/session.py:157` — `except Exception: pass` swallows every
   pre-registration failure with no telemetry. Silent-failure design smell.
2. `X-Forwarded-For` / `X-Real-IP` / `Client-IP` spoofing is ported verbatim.
   Faithful to legacy, but it is deliberate provider-side evasion and should be
   an explicit, signed-off policy decision, not an inherited default.
3. No credential redaction assertion on the `details` dict inside
   `ProviderError` — it is populated from responses and returned to Core.

---

## 12. TASK BREAKDOWN

Priority-ordered. Each task is independently verifiable. **All are proposals —
nothing was executed, per §20.**

### P0

**T-01 · Unify the auto-continue ceiling**
- Delete the `getattr(config, "max_continue_attempts", 25)` fallback in
  `operations/provider_agent.py:207`; drive the outer loop from
  `limits_mod.AUTO_CONTINUE_LIMIT` only.
- Guarantee the outer loop terminates when the stream yields no
  `continue_needed` event (the current miss).
- Make `sess.continue_calls` mutate in exactly one place.
- Accept: a stubbed transport that never emits `continue_needed` produces
  ≤5 continue requests.

**T-02 · Test the loop, not just the helper**
- Add a fake transport; assert request count ceiling, and assert
  `finish_reason == "auto_continue_limit_reached"` on exhaustion.
- Accept: T-02 fails against today's code and passes after T-01.

### P1

**T-03 · Wire `fileInfos` through session pre-registration**
- Give `create_chat_session()` a `sources` parameter; populate via the existing
  `assets/upload.build_native_files_payload()`.
- Accept: payload snapshot test matches the legacy 7-field shape.

**T-04 · Reconcile `file_upload` / `vision_input` with reality**
- Either wire an upload path, or demote both to `PARTIALLY_SUPPORTED` in
  `manifest.yaml` + `discovery/capabilities.py` with the blocker recorded.
- Accept: a test asserts every `CONFIRMED` capability has a reachable code path.

**T-05 · Build the mock transport layer**
- Shared fixture injecting scripted SSE/HTTP responses. Unblocks T-02 and all
  of §8. Highest structural leverage in this list.

### P2

**T-06 · Session ownership & concurrency** — add tenant/user identity to
`ConversationSession`; cap `_continue_stream` recursion; concurrency test.
**T-07 · Replace silent excepts** — surface `session.py:157` failures as
telemetry instead of `pass`.
**T-08 · Document the gaps** — record GAP-01/02/03 in
`_pending_real_providers.md`; they are currently invisible.
**T-09 · Decide on `active_session.txt`** — port or formally declare dropped.
**T-10 · Policy sign-off on IP spoofing headers.**

### P3

**T-11 · Redaction assertion on `ProviderError.details`.**
**T-12 · Attachment discovery** (`scan_attachments_folder` equivalent) — only if
Core wants folder-drop semantics.

### Dependency order

```text
T-05 ──► T-02 ──► T-01        (mock first, then the P0 fix is verifiable)
T-05 ──► T-03, T-04
T-08 can start immediately (documentation only)
```

---

## 13. Reference-Readiness Gate

Not reference-ready until: T-01…T-05 land, then live-credential contract runs,
then security review items 9/10/14. Flipping `status: disabled` remains a
separate, deliberate decision — `test_provider_is_disabled_until_verified` will
fail on purpose at that moment.
