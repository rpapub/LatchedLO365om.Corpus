"""Interactive token acquisition via MSAL public client flow.

Supports personal Microsoft accounts (consumers) and work/school accounts.
Tokens are cached on disk so re-authentication is only required when the
cache is absent or the token has expired.

Environment variables:
    CORPUS_CLIENT_ID    Azure AD app registration client ID
    CORPUS_TENANT_ID    Tenant ID or well-known name: common | consumers | organizations
"""

import os
from pathlib import Path

import msal

SCOPES = ["https://graph.microsoft.com/Mail.ReadWrite"]

# Token cache lives next to the package in the user's local app data
_CACHE_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) \
    / "cpmf_lo365om_corpus" / "token_cache.json"


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if _CACHE_PATH.exists():
        cache.deserialize(_CACHE_PATH.read_text(encoding="utf-8"))
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(cache.serialize(), encoding="utf-8")


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
    cache = _load_cache()

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache,
    )

    # Try silent acquisition from cache first
    accounts = app.get_accounts()
    result = None
    if accounts:
        print(f"  Attempting silent token refresh for {accounts[0]['username']} ...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # Fall back to interactive browser flow
    if not result:
        print("  Opening browser for interactive sign-in ...")
        result = app.acquire_token_interactive(scopes=SCOPES)

    _save_cache(cache)

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
    cache = _load_cache()

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache,
    )

    # Try silent acquisition from cache first
    accounts = app.get_accounts()
    result = None
    if accounts:
        print(f"  Attempting silent token refresh for {accounts[0]['username']} ...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # Fall back to device code flow
    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow initiation failed: {flow.get('error_description')}")
        print()
        print(flow["message"])   # prints: "To sign in, use a web browser to open https://microsoft.com/devicelogin and enter the code XXXXXXXX"
        print()
        result = app.acquire_token_by_device_flow(flow)  # blocks until user completes sign-in

    _save_cache(cache)

    if "access_token" not in result:
        error = result.get("error_description") or result.get("error") or str(result)
        raise RuntimeError(f"Token acquisition failed: {error}")

    print(f"  Authenticated as: {result.get('id_token_claims', {}).get('preferred_username', '?')}")
    return result["access_token"]
