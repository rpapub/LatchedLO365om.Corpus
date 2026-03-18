# cpmf-lo365om-corpus

Creates test fixture messages in a Microsoft 365 mailbox so that
[LatchedLO365om](https://github.com/rpapub/LatchedLO365om) consumers can run
[LatentLithium](https://github.com/rpapub/LatentLithium) test cases against real
Graph API data.

---

## Install uv

`uvx` is part of [uv](https://docs.astral.sh/uv/) — a fast Python package runner.
No Python installation is required separately; uv manages everything.

**Windows (recommended):**
```powershell
winget install astral-sh.uv
```

**Or via the uv installer script:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, restart your terminal and verify:
```powershell
uvx --version
```

### Linux only — system libraries required

The token cache uses libsecret for encryption on Linux. See [Linux prerequisites](#linux-prerequisites) at the end of this document.

> On macOS and Windows no extra system libraries are needed.

---

## Prerequisites

### Microsoft 365 account

A personal (Outlook.com / Hotmail) or work/school (Entra ID) account with
access to a mailbox you can use for testing.
Use a **dedicated test mailbox** — the `setup` command clears the target folder on every run.

### Entra ID app registration (one-time)

1. Go to [portal.azure.com](https://portal.azure.com) → **Entra ID** → **App registrations** → **New registration**
2. Name it anything (e.g. `corpus-cli`)
3. Under **Redirect URIs** → add `http://localhost` (platform: **Public client / native**)
4. Under **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated** → `Mail.ReadWrite`
5. If your tenant requires it: **Grant admin consent**
6. Copy the **Application (client) ID** — you will need it below

For **personal Outlook.com / Hotmail accounts**, use `consumers` as the tenant ID.

---

## Environment variables

Set these in your shell before running any command, or pass them as flags.

```powershell
$env:CORPUS_CLIENT_ID = "<application-client-id>"
$env:CORPUS_TENANT_ID = "consumers"          # or your Entra tenant ID / domain
$env:CORPUS_MAILBOX   = "you@outlook.com"    # mailbox where fixtures are created
```

| Variable | Description |
|---|---|
| `CORPUS_CLIENT_ID` | App registration client ID |
| `CORPUS_TENANT_ID` | Tenant ID, domain, or `consumers` for personal accounts |
| `CORPUS_MAILBOX` | Target mailbox email address |

---

## Workflow

### 1 — Authenticate

Opens a browser window for interactive sign-in and caches the token locally.

```powershell
uvx cpmf-lo365om-corpus auth
```

### 2 — Create corpus messages

Reads a scenario yaml, creates fixture messages in the mailbox, and writes
`corpus.json` — the manifest consumed by LatentLithium test cases.

```powershell
uvx cpmf-lo365om-corpus setup `
    --corpus scenarios\mail-demo.yaml `
    --output corpus.json
```

Re-run `setup` any time you need a fresh corpus — the target folder is cleared and
re-populated on every run.

### 3 — Run tests

Open LatentLithium in UiPath Studio and point it at your `corpus.json`.

### 4 — Tear down

Deletes all messages created during `setup` using the IDs recorded in `corpus.json`.

```powershell
uvx cpmf-lo365om-corpus teardown --manifest corpus.json
```

---

## Command reference

```
uvx cpmf-lo365om-corpus auth     [--client-id …] [--tenant-id …]
uvx cpmf-lo365om-corpus setup    [--corpus PATH] [--output PATH] [--mailbox …]
uvx cpmf-lo365om-corpus teardown [--manifest PATH]
```

All flags can be replaced by the corresponding environment variable (see table above).

---

## Scenario yaml

Corpus messages are defined in a scenario yaml file.
See [`corpus.schema.yaml`](corpus.schema.yaml) for the full schema and
[`scenarios/mail-demo.yaml`](scenarios/mail-demo.yaml) for a working example.

---

## Linux prerequisites

The token cache is encrypted using [libsecret](https://wiki.gnome.org/Projects/Libsecret)
via PyGObject. The following system libraries must be installed before running any command.

Tested on Ubuntu 24.04 (including WSL2):

```bash
sudo apt update
sudo apt install libgirepository1.0-dev gir1.2-secret-1 python3-cairo-dev
sudo apt install libcairo2-dev
sudo apt install libgirepository-2.0-dev
```

These are one-time system-level installs. After installing, `uvx` will compile and
cache PyGObject automatically on first run.
