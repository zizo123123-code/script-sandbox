# Providers

SPEC: `01_30_PROVIDER_ARCHITECTURE_AND_PLUGIN_SPEC.md`
      `01_31_PROVIDER_SCAFFOLDING_AND_ONBOARDING.md` §5

## Layout

```
providers/
├── README.md                       ← this file
├── _pending_real_providers.md       ← activation state (31 §9)
└── real/
    └── notegpt/                     ← real provider, status: disabled
        ├── manifest.yaml
        ├── provider.py              ← the ONLY Core-facing surface
        ├── client.py                ← provider-internal facade
        ├── config.py
        ├── errors.py
        ├── runtime/                 ← auth, request, session, parser, errors
        ├── operations/              ← 3 implemented + 6 not-applicable
        ├── discovery/               ← models, capabilities, limits
        ├── account/                 ← 1 implemented + 5 not-applicable
        ├── assets/                  ← upload (both paths blocked), download
        ├── pool/                    ← 7 not-applicable stubs
        ├── provider_health/         ← monitor, circuit breaker
        └── tests/                   ← 44 offline contract tests
```

The `registry/`, `common/`, and `templates/` directories from 31 §5 are not
present in this repo. This repo currently holds the specifications plus the
first real provider; the shared scaffold lives in the platform Core repo. The
provider is written so that no Core module is required for it to be imported,
validated, or tested.

## The boundary rule

30 §2 — **the Core must not import provider internals.**

```python
from providers.real.notegpt import NoteGPTProvider   # allowed
from providers.real.notegpt.runtime.auth import login  # NOT allowed from Core
```

`providers/real/notegpt/__init__.py` exports exactly
`["NoteGPTProvider", "get_provider"]`, and a contract test asserts that list
does not grow.

## Provider status

| Provider | Status | Routable |
|---|---|---|
| `notegpt` | `disabled` | no |

Nothing here is routable. `is_functional: false` excludes a provider from
execution (31 §10), and the adapter additionally raises
`ProviderDisabledError` from its activation gate, so a misconfigured router
cannot execute a declared operation by accident.

## Running the contract tests

```bash
# with pytest
python3 -m pytest providers/real/notegpt/tests/ -v

# without pytest
python3 providers/real/notegpt/tests/test_contract.py
```

These tests make **no network calls**. They verify the contract — manifest
validity, tri-state capabilities, error normalization, model catalog,
unsupported-operation rejection, secret redaction, and Core isolation.

They do not verify that generation works. Per 31 §11, *"Do not write tests
that pretend generation works"* — and that gap is precisely why the provider
stays disabled. See `_pending_real_providers.md` for what live verification
still requires.

## Evidence discipline

Every factual claim in this provider traces to `inventory/notegpt/`, and where
the inventory was wrong, to `CORRECTIONS.md` / `CORRECTIONS_ROUND2.md`. Four
corrections shaped the code more than anything else:

- **Success code is `100000`, not `0`** (CORRECTIONS §3). `code: 0` appears
  zero times in 916 HAR entries.
- **App code beats HTTP 200** (CORRECTIONS §3). An expired session arrives as
  HTTP 200 with `{"code": 164003}`; reading the status line alone reports
  success on a failed request.
- **The `text` SSE event carries the answer** (ROUND2 §2). It was missing from
  every source document and from the first corrections pass — dropping it
  drops the response.
- **The account pool does not exist** (CORRECTIONS §7). `manifest.yaml`
  declares `account_pool.supported: false`; recovery is `rotate_identity()`
  on a single account, preserving `conversation_id`.

Unproven claims are `"unknown"`, never `false`. A negative capability claim
needs conclusive proof (CORRECTIONS §13), so `video_generation` and
per-model `vision_input` are reported as unknown rather than unsupported.
The 7 invented model IDs are excluded from bindings and rejected at resolution
time with `reason: "phantom_model"`.

Two further findings are worth calling out, because both are cases where the
"obvious" implementation would have been wrong:

- **File upload is deliberately not implemented.** Two paths exist and
  *neither* is usable here. The official path
  (`/api/v1/upload/sign-url` → `PUT` to Alibaba OSS) appears once in the HAR
  but `grep -c "sign-url"` in the reference script is **0**, and its request
  body carries an HMAC `sign` field whose derivation is unknown. The path the
  script actually runs (ROUND2 §3) uploads every attachment to
  **`tmpfiles.org`** — a public third-party host — making user files publicly
  reachable. `upload.py` therefore refuses by default and requires an explicit
  `allow_third_party_transit=True` opt-in rather than quietly exfiltrating data.
- **`164003` and `164002` recover by rotation, not re-login.** `01.06:798`
  groups all three app codes into a single branch calling
  `rotate_identity(keep_conversation=True)`; it never calls `login()`. The
  categories still distinguish quota from auth, but the recovery hint follows
  observed behavior, with `reauthenticate` recorded as an unverified fallback.
