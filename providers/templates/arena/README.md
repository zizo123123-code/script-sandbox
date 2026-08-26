# Arena.ai Provider Template

This directory is a **disabled Type L provider template**, not a live
Arena.ai integration.

## Deliberate guarantees

- `status: template_disabled` and `is_functional: false` are permanent until
  a real contract is supplied and verified.
- No Arena endpoint, model ID, API key format, cookie, token, rate limit, or
  event schema is guessed.
- The adapter has no HTTP client and every execution request returns a
  normalized `provider_disabled` error.
- The manifest keeps the provider-agent shape (`provider_agent`, `tool_use`,
  and `files`) visible for future onboarding, but `is_routable()` and the
  routing capability view stay false/empty.
- Credentials, if ever configured, must be passed as an opaque reference from
  an approved secret store; values are never written to this tree or logs.

## Activation checklist

Before converting this template to a real provider, supply and verify:

1. Provider API and authentication contract.
2. Capability and model evidence.
3. Agent lifecycle and event schema.
4. Error and rate-limit mappings.
5. Tenant/tool policy and audit boundaries.
6. Contract tests, security review, and approved admin enablement.

Until then, this package exists only for schema inspection and safe contract
testing. It must not be routed or described as Arena.ai execution.
