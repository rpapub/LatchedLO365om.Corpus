"""CLI entry point for cpmf-lo365om-corpus.

Usage:
    python -m cpmf_lo365om_corpus.cli setup   [options]
    python -m cpmf_lo365om_corpus.cli teardown [options]

Environment variables:
    CORPUS_TOKEN    Bearer token (alternative to --token)
    CORPUS_MAILBOX  Mailbox email (alternative to --mailbox)
"""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

from .auth import acquire_token_interactive, acquire_token_device_flow
from .context import make_run_context, make_context
from .graph import make_client, ensure_folder, clear_folder, create_message, write_extension
from .manifest import build_manifest


# ── setup ──────────────────────────────────────────────────────────────────────

def cmd_setup(args):
    corpus_path = Path(args.corpus)
    output_path = Path(args.output)
    repo_root   = corpus_path.parent.parent.parent  # Tests/Corpus/corpus.yaml → repo root

    print(f"Loading scenario: {corpus_path}")
    with corpus_path.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    run_id, timestamp, date = make_run_context()
    print(f"Run ID:  {run_id}")
    print(f"Mailbox: {args.mailbox}")

    scenario  = spec.get("scenario", {})
    workload  = scenario.get("workload", "mail")
    fixtures  = spec.get("fixtures", {})
    expected  = spec.get("expected", {})
    execution = spec.get("execution", {})
    setup_cfg = execution.get("setup", {})

    client = make_client(args.token)

    # Ensure all required folders
    folder_path = (setup_cfg.get("ensure_folders") or ["TestCorpus/Mail"])[0]
    print(f"\nEnsuring folder: {folder_path}")
    folder_id = ensure_folder(client, args.mailbox, folder_path)

    print("\nClearing existing messages...")
    deleted = clear_folder(client, args.mailbox, folder_id)
    print(f"  deleted {deleted} messages")

    messages_created = []
    print("\nCreating corpus messages...")

    mail_fixtures = fixtures.get("mail", [])
    for i, msg_spec in enumerate(mail_fixtures):
        label = msg_spec["label"]
        ctx   = make_context(run_id, timestamp, date, label=label, index=i)
        print(f"  [{i:02d}] {label} ...", end=" ", flush=True)

        msg_id = create_message(client, args.mailbox, folder_id, msg_spec, ctx, repo_root)

        if "extension" in msg_spec:
            write_extension(client, args.mailbox, msg_id, msg_spec["extension"], ctx)
            print("ok (ext)")
        else:
            print("ok")

        messages_created.append({
            "label":        label,
            "immutable_id": msg_id,
            "msg_spec":     msg_spec,
            "ctx":          ctx,
        })

    manifest = build_manifest(
        run_id=run_id,
        timestamp=timestamp,
        mailbox=args.mailbox,
        workload=workload,
        folder_path=folder_path,
        messages_created=messages_created,
        expected_spec=expected,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to: {output_path}")
    print(f"Messages created:    {len(messages_created)}")


# ── teardown ───────────────────────────────────────────────────────────────────

def cmd_teardown(args):
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"No manifest found at {manifest_path} — nothing to tear down.")
        return

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    client   = make_client(args.token)
    mailbox  = manifest["mailbox"]
    folder   = manifest["folder"]

    print(f"Teardown: {folder} in {mailbox}")
    # Resolve folder id then delete all messages
    from .graph import ensure_folder
    folder_id = ensure_folder(client, mailbox, folder)
    deleted = clear_folder(client, mailbox, folder_id)
    print(f"  deleted {deleted} messages")


# ── argument parsing ───────────────────────────────────────────────────────────

def _common_auth(parser):
    parser.add_argument("--auth",      default="token", choices=["token", "interactive", "device"],
                        help="Auth mode: 'token' (env/flag), 'interactive' (MSAL browser), 'device' (device code — for WSL/headless)")
    parser.add_argument("--token",     default=os.environ.get("CORPUS_TOKEN"),     help="Bearer token (auth=token)")
    parser.add_argument("--client-id", default=os.environ.get("CORPUS_CLIENT_ID"), help="App registration client ID (auth=interactive)")
    parser.add_argument("--tenant-id", default=os.environ.get("CORPUS_TENANT_ID", "consumers"), help="Tenant ID or 'consumers' (auth=interactive)")
    parser.add_argument("--mailbox",   default=os.environ.get("CORPUS_MAILBOX"),   help="Mailbox email")


def main():
    parser = argparse.ArgumentParser(
        prog="cpmf-lo365om-corpus",
        description="LatentLithium corpus setup / teardown",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # setup
    p_setup = sub.add_parser("setup", help="Create corpus messages and write manifest")
    p_setup.add_argument("--corpus", default="Tests/Corpus/corpus.yaml", help="Path to scenario yaml")
    p_setup.add_argument("--output", default="Tests/Corpus/corpus.json",  help="Path to write corpus.json")
    _common_auth(p_setup)

    # teardown
    p_tear = sub.add_parser("teardown", help="Delete corpus messages based on manifest")
    p_tear.add_argument("--manifest", default="Tests/Corpus/corpus.json", help="Path to corpus.json")
    _common_auth(p_tear)

    args = parser.parse_args()

    # Resolve token
    if args.auth in ("interactive", "device"):
        if not args.client_id:
            print("ERROR: --client-id or CORPUS_CLIENT_ID is required for interactive/device auth", file=sys.stderr)
            sys.exit(1)
        if args.auth == "device":
            print("Acquiring token via device code flow ...")
            args.token = acquire_token_device_flow(args.client_id, args.tenant_id)
        else:
            print("Acquiring token interactively ...")
            args.token = acquire_token_interactive(args.client_id, args.tenant_id)
    elif not args.token:
        print("ERROR: --token or CORPUS_TOKEN is required (or use --auth interactive)", file=sys.stderr)
        sys.exit(1)

    if not args.mailbox:
        print("ERROR: --mailbox or CORPUS_MAILBOX is required", file=sys.stderr)
        sys.exit(1)

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "teardown":
        cmd_teardown(args)


if __name__ == "__main__":
    main()
