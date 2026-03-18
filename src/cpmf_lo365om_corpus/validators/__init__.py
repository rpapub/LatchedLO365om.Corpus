"""Validators for corpus scenario yaml files."""

import jsonschema

from .scenario_schema import SCENARIO_SCHEMA


def validate_scenario(spec: dict, path: str = "<scenario>") -> None:
    """Validate a parsed scenario yaml dict against the corpus schema.

    Args:
        spec:  Parsed yaml content (dict).
        path:  File path for error messages.

    Raises:
        SystemExit on validation failure — prints all errors and exits.
    """
    validator = jsonschema.Draft202012Validator(SCENARIO_SCHEMA)
    errors = sorted(validator.iter_errors(spec), key=lambda e: list(e.absolute_path))

    if not errors:
        return

    print(f"Schema validation failed for: {path}")
    for err in errors:
        location = " → ".join(str(p) for p in err.absolute_path) or "(root)"
        print(f"  [{location}] {err.message}")

    import sys
    sys.exit(1)
