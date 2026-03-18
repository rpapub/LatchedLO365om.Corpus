# ADR 0003 — Scenario yaml shape and file location

**Status:** Accepted
**Date:** 2026-03-18

---

## Context

The corpus tooling needs one or more yaml files to declare test fixtures and expected
outcomes. Two questions require explicit decisions:

1. **Shape** — what top-level blocks does a scenario yaml contain, and what is valid inside
   each block?
2. **Location** — where do scenario yaml files live, and does that change as the project
   matures?

---

## Decision

### Shape

A scenario yaml has five top-level blocks.

```
scenario       — identity and workload classification
fixtures       — declarative test data per workload type
expected       — observable outcomes per label
execution      — setup / teardown policy
tests          — which UiPath test cases belong to this scenario
```

#### `scenario`

```yaml
scenario:
  name: "mail-basic"      # stable identifier, used in manifest
  workload: mail          # mail | files (future)
```

#### `fixtures`

Fixtures are grouped by workload type. The `mail` list contains message declarations;
`files` is reserved for future SharePoint/OneDrive fixtures.

Each mail fixture declares:

```yaml
fixtures:
  mail:
    - label: MSG_FORM_BASIC           # UPPER_SNAKE_CASE, unique within scenario
      subject: "..."                  # supports {template} variables
      body:                           # see Body shape below
        ...
      importance: normal | high | low
      isRead: false | true
      attachments: []                 # see Attachment shape below
      extension:                      # optional OpenTypeExtension
        name: "..."
        act: { ... }

  files: []               # placeholder — SharePoint fixture shape TBD
```

##### Body shape

Three forms are supported, in order of increasing structure:

```yaml
# 1. No body
body: null

# 2. Raw shorthand — for fixtures that don't require extraction testing
body:
  contentType: text | html
  content: "plain string, supports {template} variables"

# 3. Compositional sections — for structured body content
body:
  contentType: text
  sections:
    - type: header
      content: "Preamble text\n"
    - type: structured
      separator: ": "         # optional, defaults to ": "
      fields:
        - key: "Field Name"
          value: "literal string"          # or a generation spec:
        - key: "Company"
          value:
            strategy: faker
            method: company
            locale: de_DE
            seed: 42                       # optional, for reproducibility
    - type: footer
      content: "\nClosing text"
```

The `separator` declared in a `structured` section is written into `corpus.json` alongside
the resolved field values, so test XAML can configure BodyFieldExtractor rules correctly
without re-parsing the body text.

##### Attachment shape

```yaml
attachments:
  - name: "filename_{date}.pdf"     # supports {template} variables
    strategy: generate_pdf | generate_xlsx | generate_text | random_bytes | fixture_file
    # strategy-specific keys follow:
    pages: [...]                    # generate_pdf
    sheets: [...]                   # generate_xlsx
    content: "..."                  # generate_text
    size_kb: 512                    # random_bytes
    path: "relative/path"           # fixture_file — relative to repo root
```

#### `expected`

Free-form string keys per label. Test XAML reads only the keys it cares about.

```yaml
expected:
  MSG_FORM_BASIC:
    retrieval:
      isRead: false
      importance: normal
    bodyExtraction:
      values:
        emailaddress: "alice@example.com"
      unmatchedFields: ["unknownfield"]
      missingRequiredKeys: []
    eml:
      fileCount: 1
      minSizeBytes: 512
    attachments:
      count: 2
      minSizeBytes: 512
    move_to_processed:
      targetFolder: "TestCorpus/Mail/Processed"
```

#### `execution`

```yaml
execution:
  setup:
    ensure_folders:
      - "TestCorpus/Mail"       # created if absent, idempotent
    idempotent: true            # existing messages cleared before creation
  teardown:
    policy: delete              # delete | keep (keep = leave messages for inspection)
```

#### `tests`

```yaml
tests:
  - Mail_GetMessages
  - Mail_ExtractBodyFields
  - Mail_SaveAllAsEml
  - Mail_SaveAllAttachments
  - Mail_MoveMessage
  - Mail_WriteReadMessageExtension
```

This list is **documentation** — it records which UiPath test cases depend on this scenario.
It is not processed by the setup script. Future tooling may use it for test selection or
reporting.

---

### What the yaml does NOT contain

- **Credentials** — no token, no mailbox address, no tenant ID. All environment binding is
  done at runtime via `CORPUS_TOKEN`, `CORPUS_MAILBOX` (env vars) or CLI flags.
- **Application IDs** — these are Orchestrator Assets or env vars, not test data.
- **Live IDs** — no ImmutableIds, no folder IDs. These appear only in `corpus.json`.

---

### Location

#### Interim: LatentLithium (library self-tests)

During library development, scenario yaml files live inside the LatentLithium test repo:

```
LatentLithium/
  Tests/
    Corpus/
      corpus.yaml             # default scenario (mail-basic)
      corpus-eml.yaml         # future: EML-focused scenario
      corpus.json             # generated — gitignored
      docs/
        adr/
      src/
        cpmf_lo365om_corpus/  # the setup package
      pyproject.toml
```

Multiple scenario files may coexist. Each produces its own manifest when run:

```bash
python -m cpmf_lo365om_corpus.cli setup --corpus Tests/Corpus/corpus-eml.yaml \
                                         --output Tests/Corpus/corpus-eml.json
```

#### Target: RPA Process repo (consumer)

When an RPA process built on LatchedLO365om needs its own integration tests, it brings its
own scenario yaml. The package is installed as a dev dependency; the yaml and manifest live
alongside the process test suite:

```
MyRpaProcess/
  Tests/
    Corpus/
      corpus.yaml             # process-specific scenario
      corpus.json             # generated — gitignored
  pyproject.toml              # or requirements-dev.txt
```

The scenario yaml in the process repo declares fixtures and expected values specific to that
process's domain (its own mailbox folders, its own form fields, its own attachment types).
It does not reference or import from LatentLithium's scenario files.

#### Future: `rpapub/LatchedLO365om.Corpus` repository

As the tooling stabilises, `cpmf-lo365om-corpus` will move to a dedicated repository
(`rpapub/LatchedLO365om.Corpus`) and be published to PyPI (or a private index). Consumer
repos install it as a versioned dependency. LatentLithium's `Tests/Corpus/` then contains
only yaml files and the generated manifest, not the package source.

---

## Consequences

- Scenario yaml files are safe to commit — no credentials, no live IDs.
- `corpus.json` is gitignored — it is ephemeral, regenerated before each test run.
- The yaml shape is stable enough to write against today; the package version pins ensure
  consumers are not broken by schema evolution.
- New workloads (e.g. SharePoint files) extend the `fixtures` block without changing the
  other four top-level blocks.
- The `tests` list in the yaml provides a lightweight dependency map between corpus scenarios
  and UiPath test cases, enabling future tooling to select or report by scenario.
