# cpmf-lo365om-corpus

Corpus setup package for **LatentLithium** — the test suite for the [LatchedLO365om](https://github.com/rpapub/LatchedLO365om) UiPath library.

Reads a scenario yaml file, creates a reproducible set of mail messages in a target M365 mailbox via Graph API, and writes a `corpus.json` manifest that test cases assert against.

## Installation

```bash
cd Tests/Corpus
uv pip install -e .
```

## Usage

```bash
# Create corpus messages and write manifest
python -m cpmf_lo365om_corpus.cli setup \
  --corpus Tests/Corpus/corpus.yaml \
  --output Tests/Corpus/corpus.json

# Delete corpus messages based on manifest
python -m cpmf_lo365om_corpus.cli teardown \
  --manifest Tests/Corpus/corpus.json
```

Auth is supplied via environment variables — never in the scenario yaml:

```bash
export CORPUS_TOKEN=<bearer token>
export CORPUS_MAILBOX=<mailbox email>
```

Or via `--token` / `--mailbox` flags.

## Package structure

```
cpmf_lo365om_corpus/
  cli.py            Entry point — setup / teardown subcommands
  context.py        Template variable substitution ({run_id}, {label}, {date}, ...)
  body.py           Mail body renderer — sections: header / structured / footer
  attachments.py    Attachment generation strategies (pdf, xlsx, text, random, fixture)
  graph.py          Microsoft Graph API helpers
  manifest.py       corpus.json builder — includes expected blocks per message label
  generators/
    faker_gen.py    Faker-based value generation for structured body fields
```

## Scenario yaml

Scenarios live in `Tests/Corpus/` (one yaml per scenario). The yaml declares fixtures,
expected outcomes, execution policy, and which test cases belong to the scenario.
It never contains credentials — environment is resolved at runtime.

```yaml
scenario:
  name: "mail-basic"
  workload: mail

fixtures:
  mail:
    - label: MSG_FORM_BASIC
      subject: "Form submission basic"
      body:
        contentType: text
        sections:
          - type: header
            content: "Please process the following request:\n"
          - type: structured
            separator: ": "
            fields:
              - key: "Name"
                value: "Alice Smith"
              - key: "E-mail Address"
                value: "alice@example.com"
          - type: footer
            content: "\nThank you"
      importance: normal
      isRead: false
      attachments: []

expected:
  MSG_FORM_BASIC:
    retrieval:
      isRead: false
      importance: normal
    bodyExtraction:
      values:
        emailaddress: "alice@example.com"
      unmatchedFields: []
      missingRequiredKeys: []
    eml:
      fileCount: 1
      minSizeBytes: 512

execution:
  setup:
    ensure_folders:
      - "TestCorpus/Mail"
    idempotent: true
  teardown:
    policy: delete

tests:
  - Mail_GetMessages
  - Mail_ExtractBodyFields
  - Mail_SaveAllAsEml
```

## corpus.json manifest

The manifest is the runtime test oracle. Test XAML reads it — never the yaml.

```json
{
  "schema_version": "1",
  "run_id": "abc123",
  "created_at": "2026-03-18T05:00:00Z",
  "workload": "mail",
  "mailbox": "test@example.com",
  "folder": "TestCorpus/Mail",
  "messages": {
    "MSG_FORM_BASIC": {
      "immutableId": "AQMk...",
      "subject": "Form submission basic",
      "sourceFolder": "TestCorpus/Mail",
      "body": {
        "separator": ": ",
        "structuredFields": {
          "Name": "Alice Smith",
          "E-mail Address": "alice@example.com"
        }
      },
      "expected": {
        "retrieval": { "isRead": false, "importance": "normal" },
        "bodyExtraction": {
          "values": { "emailaddress": "alice@example.com" },
          "unmatchedFields": [],
          "missingRequiredKeys": []
        },
        "eml": { "fileCount": 1, "minSizeBytes": 512 }
      }
    }
  }
}
```

## Value generation

Field values in `structured` sections support faker-based generation:

```yaml
fields:
  - key: "Company"
    value:
      strategy: faker
      method: company
      locale: de_DE
      seed: 42
```

Resolved values are written into `corpus.json` so expected assertions remain deterministic.

## Related

- [LatchedLO365om](https://github.com/rpapub/LatchedLO365om) — UiPath M365 library under test
- [LatentLithium](https://github.com/rpapub/LatentLithium) — UiPath test suite (parent repo)
- Issues [#23](https://github.com/rpapub/LatchedLO365om/issues/23), [#27](https://github.com/rpapub/LatchedLO365om/issues/27) — corpus design tracking
