"""Microsoft Graph API helpers."""

import json

import httpx

from .attachments import build_attachment
from .body import build_body
from .context import t, t_deep

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def graph_get(client: httpx.Client, url: str) -> dict:
    r = client.get(url)
    r.raise_for_status()
    return r.json()


def graph_post(client: httpx.Client, url: str, body: dict) -> dict:
    r = client.post(url, json=body)
    r.raise_for_status()
    return r.json()


def graph_patch(client: httpx.Client, url: str, body: dict) -> dict:
    r = client.patch(url, json=body)
    r.raise_for_status()
    return r.json()


def graph_delete(client: httpx.Client, url: str) -> None:
    r = client.delete(url)
    if r.status_code not in (200, 204, 404):
        r.raise_for_status()


def ensure_folder(client: httpx.Client, mailbox: str, folder_path: str) -> str:
    """
    Ensure a nested folder path exists (e.g. 'TestCorpus/Mail'), creating
    each segment if absent. Returns the folder ID of the deepest folder.
    """
    base = f"{GRAPH_BASE}/users/{mailbox}/mailFolders"
    segments = folder_path.split("/")
    parent_id = None

    for segment in segments:
        if parent_id is None:
            url = f"{base}?$filter=displayName eq '{segment}'&$select=id,displayName"
        else:
            url = f"{base}/{parent_id}/childFolders?$filter=displayName eq '{segment}'&$select=id,displayName"

        data = graph_get(client, url)
        existing = data.get("value", [])

        if existing:
            parent_id = existing[0]["id"]
            print(f"  folder exists: {segment} ({parent_id[:16]}...)")
        else:
            if parent_id is None:
                created = graph_post(client, base, {"displayName": segment})
            else:
                created = graph_post(client, f"{base}/{parent_id}/childFolders", {"displayName": segment})
            parent_id = created["id"]
            print(f"  folder created: {segment} ({parent_id[:16]}...)")

    return parent_id


def clear_folder(client: httpx.Client, mailbox: str, folder_id: str) -> int:
    """Delete all messages in the folder. Returns count deleted."""
    url = f"{GRAPH_BASE}/users/{mailbox}/mailFolders/{folder_id}/messages?$select=id&$top=50"
    deleted = 0
    while url:
        data = graph_get(client, url)
        for msg in data.get("value", []):
            graph_delete(client, f"{GRAPH_BASE}/users/{mailbox}/messages/{msg['id']}")
            deleted += 1
        url = data.get("@odata.nextLink")
    return deleted


def create_message(client: httpx.Client, mailbox: str, folder_id: str,
                   msg_spec: dict, ctx: dict, repo_root) -> str:
    """Create a message in the folder and return its ImmutableId."""
    body_spec = msg_spec.get("body")
    content_type, content = build_body(body_spec, ctx)

    payload = {
        "subject": t(msg_spec["subject"], ctx),
        "body": {
            "contentType": content_type,
            "content": content,
        },
        "from": {
            "emailAddress": {"address": mailbox, "name": "LatentLithium Corpus"},
        },
        "importance": msg_spec.get("importance", "normal"),
        "isRead": msg_spec.get("isRead", False),
    }

    attachments = msg_spec.get("attachments", [])
    if attachments:
        payload["attachments"] = [build_attachment(a, ctx, repo_root) for a in attachments]

    url = f"{GRAPH_BASE}/users/{mailbox}/mailFolders/{folder_id}/messages"
    result = graph_post(client, url, payload)
    return result["id"]


def write_extension(client: httpx.Client, mailbox: str, msg_id: str, ext_spec: dict, ctx: dict) -> None:
    """Write an OpenTypeExtension to a message."""
    body = {
        "@odata.type": "microsoft.graph.openTypeExtension",
        "extensionName": t(ext_spec["name"], ctx),
        "act": json.dumps(t_deep(ext_spec["act"], ctx)),
    }
    url = f"{GRAPH_BASE}/users/{mailbox}/messages/{msg_id}/extensions"
    graph_post(client, url, body)


def make_client(token: str) -> httpx.Client:
    return httpx.Client(
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Prefer":        'IdType="ImmutableId"',
        },
        timeout=30,
    )
