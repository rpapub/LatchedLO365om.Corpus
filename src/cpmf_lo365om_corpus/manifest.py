"""Build corpus.json manifest from resolved spec + Graph responses."""

from .body import extract_structured_fields, get_separator
from .context import t


SCHEMA_VERSION = "1"


def build_manifest(
    run_id: str,
    timestamp: str,
    mailbox: str,
    workload: str,
    folders: dict[str, str],        # {folder_path: folder_id}
    messages_created: list[dict],   # [{label, immutable_id, msg_spec, ctx, folder_path}]
    expected_spec: dict,            # scenario["expected"] block
) -> dict:
    """
    Build the full corpus.json manifest.

    folders: all folders created/ensured during setup — path → ImmutableId.
    messages_created: list of dicts produced during setup, one per fixture message.
    expected_spec: the raw `expected` block from the scenario yaml.
    """
    messages_out = {}

    for entry in messages_created:
        label        = entry["label"]
        msg_spec     = entry["msg_spec"]
        ctx          = entry["ctx"]
        immutable_id = entry["immutable_id"]
        source_folder = entry.get("folder_path", next(iter(folders), ""))

        body_spec = msg_spec.get("body")
        structured_fields = extract_structured_fields(body_spec, ctx) if body_spec else {}
        separator = get_separator(body_spec) if body_spec else ": "

        messages_out[label] = {
            "immutableId":  immutable_id,
            "subject":      t(msg_spec["subject"], ctx),
            "sourceFolder": source_folder,
            "body": {
                "separator":        separator,
                "structuredFields": structured_fields,
            },
            "expected": expected_spec.get(label, {}),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id":         run_id,
        "created_at":     timestamp,
        "workload":       workload,
        "mailbox":        mailbox,
        "folders":        folders,          # {path: folder_id} — all ensured folders
        "messages":       messages_out,
    }
