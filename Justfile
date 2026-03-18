# cpmf-lo365om-corpus development commands

# List available commands
default:
    @just --list

# Install in editable mode
install:
    uv pip install -e .

# Run unit tests
test:
    uv run pytest tests/unit -m "not integration"

# Run integration tests (requires CORPUS_TOKEN + CORPUS_MAILBOX env vars)
test-integration:
    uv run pytest -m integration

# Build wheel + sdist, then validate with twine
build:
    uv build
    uv run twine check dist/*

# Upload to TestPyPI
publish-test:
    twine upload --repository testpypi dist/*

# Upload to PyPI
publish:
    twine upload dist/*

# Acquire a fresh token and write it to .token (device code flow)
token client_id mailbox:
    CORPUS_CLIENT_ID={{client_id}} CORPUS_MAILBOX={{mailbox}} \
        uv run python -m cpmf_lo365om_corpus.cli auth --auth device

# Create corpus messages (requires .env or env vars)
setup scenario="scenarios/mail-demo.yaml" output="corpus.json":
    uv run python -m cpmf_lo365om_corpus.cli setup \
        --corpus {{scenario}} --output {{output}}

# Tear down corpus messages from last run
teardown manifest="corpus.json":
    uv run python -m cpmf_lo365om_corpus.cli teardown --manifest {{manifest}}
