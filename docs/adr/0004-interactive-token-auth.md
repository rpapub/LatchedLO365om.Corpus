# ADR 0004 — Interactive token acquisition via MSAL

**Status:** Accepted
**Date:** 2026-03-18

---

## Context

The corpus setup script must authenticate to Microsoft Graph to create and delete mailbox
messages. Authentication requires a bearer token. Two acquisition strategies were considered:

1. **Pre-obtained token** — the caller acquires a token externally (e.g. via `az` CLI,
   Postman, or a UiPath activity) and passes it as `--token` / `CORPUS_TOKEN`.
2. **MSAL interactive browser flow** — the script opens the system browser, the user
   signs in, and the script exchanges the auth code for a token.

---

## Decision

Both modes are supported. **Interactive (`--auth interactive`) is the default for human
operators**; token passthrough (`--auth token`) remains available for CI/CD pipelines.

Interactive auth uses the **MSAL Python public client application** with the
`acquire_token_interactive` flow, backed by a persistent on-disk token cache. Silent
refresh (no browser prompt) is attempted first on every subsequent run; the browser is
opened only when the cache is empty or the refresh token has expired.

### Why interactive over service principal / client credentials

| Concern | Interactive | Client credentials |
|---|---|---|
| Personal accounts (hotmail, outlook.com) | Supported | Not supported — Azure AD app-only tokens cannot access personal mailboxes |
| Setup complexity | App registration with public client enabled | App registration + client secret / certificate management |
| Credential in repo risk | None — token is ephemeral, cached locally | Client secret must be managed and rotated |
| Suitable for developer workstation | Yes | Overkill |
| Suitable for GitHub Actions / CI | Via device code flow (future) | Yes (future) |

Personal Microsoft accounts (`@hotmail.com`, `@outlook.com`) do not support
client credentials flow for delegated Graph scopes (`Mail.ReadWrite`). Interactive
or device code flow is the only viable path for personal account testing.

### Token cache

Tokens are cached in:
```
%LOCALAPPDATA%\cpmf_lo365om_corpus\token_cache.json   (Windows)
~/.local/share/cpmf_lo365om_corpus/token_cache.json   (Linux/macOS)
```

The cache is **not committed to the repository** (`.gitignore` covers `*.json` outside
`Tests/Corpus/docs/`). Refresh tokens in the cache allow silent re-authentication for the
lifetime of the refresh token (typically 90 days for personal accounts).

### CLI interface

```bash
# Interactive (browser opens on first run)
python -m cpmf_lo365om_corpus.cli setup \
  --auth interactive \
  --client-id <app-registration-id> \
  --tenant-id consumers \
  --mailbox rpapub@hotmail.com \
  --corpus Tests/Corpus/corpus-demo.yaml \
  --output Tests/Corpus/corpus-demo.json

# Token passthrough (CI/CD)
python -m cpmf_lo365om_corpus.cli setup \
  --auth token \
  --mailbox rpapub@hotmail.com
# CORPUS_TOKEN and CORPUS_MAILBOX can be set via env vars
```

Environment variable equivalents:

| Flag | Env var | Notes |
|---|---|---|
| `--token` | `CORPUS_TOKEN` | Pre-obtained bearer token |
| `--client-id` | `CORPUS_CLIENT_ID` | App registration client ID |
| `--tenant-id` | `CORPUS_TENANT_ID` | Defaults to `consumers` |
| `--mailbox` | `CORPUS_MAILBOX` | Target mailbox address |

### Required app registration

A public client app registration in Azure AD / Entra ID is required:
- Platform: **Mobile and desktop applications** (enables public client flow)
- Redirect URI: `http://localhost` (MSAL default for interactive)
- API permissions: `Mail.ReadWrite` (delegated) — user consent, no admin consent needed
  for personal accounts
- **No client secret** — public client only

The app registration client ID is not a credential and may be committed to the repo or
stored in an environment variable.

---

## Consequences

- Developers running corpus setup on a workstation authenticate interactively once;
  subsequent runs are silent until the refresh token expires.
- The `--auth token` path is preserved for future GitHub Actions integration (token
  injected via `CORPUS_TOKEN` secret).
- A device code flow variant (`acquire_token_by_device_flow`) can be added to `auth.py`
  for headless CI environments without a browser — deferred until needed.
- The token cache file must be excluded from version control. It is covered by `.gitignore`.
- Client credentials flow is explicitly out of scope for personal account scenarios.
