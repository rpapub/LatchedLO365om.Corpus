"""Interactive token acquisition via MSAL public client flow.

Supports personal Microsoft accounts (consumers) and work/school accounts.
Tokens are cached and encrypted on disk:
  Windows : DPAPI  (%LOCALAPPDATA%\\CPMForge\\cpmf-lo365om-corpus\\TokenCache\\token_cache.bin)
  macOS   : Keychain
  Linux   : libsecret (D-Bus / gnome-keyring)

Encryption is mandatory — if the platform cannot secure the cache,
an error is raised rather than falling back to plaintext.

Environment variables:
    CORPUS_CLIENT_ID    Azure AD app registration client ID
    CORPUS_TENANT_ID    Tenant ID or well-known name: common | consumers | organizations
"""

import os
import sys
from pathlib import Path

import msal
from msal_extensions import build_encrypted_persistence, PersistedTokenCache

SCOPES = ["https://graph.microsoft.com/Mail.ReadWrite"]

_LIBRARY_NAME = "cpmf-lo365om-corpus"


def _cache_path() -> Path:
    """Return the platform-appropriate encrypted cache file path."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "CPMForge" / _LIBRARY_NAME / "TokenCache" / "token_cache.bin"


def _make_cache() -> PersistedTokenCache:
    """Build an encrypted, persisted MSAL token cache."""
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    persistence = build_encrypted_persistence(str(path))
    return PersistedTokenCache(persistence)


def acquire_token_interactive(client_id: str, tenant_id: str = "consumers") -> str:
    """
    Acquire a Graph API bearer token via MSAL interactive browser flow.

    On first call: opens the browser for sign-in.
    On subsequent calls: returns a cached / silently-refreshed token.

    Args:
        client_id:  Azure AD app registration client ID.
        tenant_id:  Tenant ID or 'consumers' (personal accounts) /
                    'organizations' / 'common'. Defaults to 'consumers'.

    Returns:
        Bearer token string.
    """
    cache = _make_cache()

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache,
    )

    accounts = app.get_accounts()
    result = None
    if accounts:
        print(f"  Attempting silent token refresh for {accounts[0]['username']} ...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        print("  Opening browser for interactive sign-in ...")
        result = app.acquire_token_interactive(scopes=SCOPES)

    if "access_token" not in result:
        error = result.get("error_description") or result.get("error") or str(result)
        raise RuntimeError(f"Token acquisition failed: {error}")

    print(f"  Authenticated as: {result.get('id_token_claims', {}).get('preferred_username', '?')}")
    return result["access_token"]


def acquire_token_device_flow(client_id: str, tenant_id: str = "consumers") -> str:
    """
    Acquire a Graph API bearer token via MSAL device code flow.

    Prints a URL and one-time code to stdout. The user opens any browser
    (e.g. on a Windows host when running from WSL) and enters the code.
    Polls until the user completes sign-in or the code expires (~15 min).

    On subsequent calls: returns a cached / silently-refreshed token.

    Args:
        client_id:  Azure AD app registration client ID.
        tenant_id:  Tenant ID or 'consumers' / 'organizations' / 'common'.

    Returns:
        Bearer token string.
    """
    cache = _make_cache()

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache,
    )

    accounts = app.get_accounts()
    result = None
    if accounts:
        print(f"  Attempting silent token refresh for {accounts[0]['username']} ...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow initiation failed: {flow.get('error_description')}")
        print()
        print(flow["message"])
        print()
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        error = result.get("error_description") or result.get("error") or str(result)
        raise RuntimeError(f"Token acquisition failed: {error}")

    print(f"  Authenticated as: {result.get('id_token_claims', {}).get('preferred_username', '?')}")
    return result["access_token"]
