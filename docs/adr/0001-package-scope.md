# ADR 0001 — Scope of `cpmf-lo365om-corpus`

**Status:** Accepted
**Date:** 2026-03-18

---

## Context

The LatchedLO365om UiPath library requires integration tests that operate against a real
Microsoft 365 mailbox. Those tests need a reproducible, well-defined set of messages to
assert against. Creating and managing that message set manually is error-prone and
non-repeatable across environments (developer machine, GitHub Runner, corporate tenant).

A Python package is needed to automate corpus lifecycle: create messages, write a manifest
that test cases can assert against, and tear down afterwards.

The question is: how broadly should this package be scoped?

---

## Decision

`cpmf-lo365om-corpus` is **scoped exclusively to LatchedLO365om**.

It is not a general-purpose M365 test fixture library. Its scenario yaml schema, manifest
shape, Graph API usage patterns, and attachment generation strategies are all designed to
support the specific test cases in LatentLithium (and, in future, in RPA process repos that
consume LatchedLO365om).

### What the package does

- Reads scenario yaml files that declare mail fixtures, expected outcomes, execution policy,
  and the list of test cases that belong to the scenario.
- Creates messages in a target M365 mailbox via Graph API using the declared fixtures.
- Writes a `corpus.json` manifest — the **runtime test oracle** — containing resolved
  ImmutableIds, resolved field values, and the full expected block per message label.
- Tears down corpus messages (deletes them from the mailbox) on demand.
- Generates attachment content (PDF, XLSX, plain text, random bytes, fixture files).
- Generates structured mail body content (header / key-value / footer sections) with
  configurable separator and optional faker-based value generation.

### What the package does NOT do

- It does not authenticate. Auth (bearer token, mailbox) is injected via environment
  variables or CLI flags — never stored in scenario yaml files.
- It does not run UiPath test cases. Test execution is orchestrated by UiPath Studio /
  Robot / Orchestrator.
- It does not validate test results. Test XAML reads `corpus.json` and asserts against it.
- It does not manage SharePoint files (yet — `files: []` is a placeholder).
- It does not provide a general M365 testing framework reusable across unrelated libraries.

---

## Consequences

- The package name (`cpmf-lo365om-corpus`) explicitly carries the library identity and will
  not be reused for unrelated projects.
- If a second CPMForge library needs corpus tooling, a new sibling package is created rather
  than generalising this one prematurely.
- The package lives in `LatentLithium` (interim) and will eventually live in a dedicated
  `rpapub/LatchedLO365om.Corpus` repository as the tooling matures.
