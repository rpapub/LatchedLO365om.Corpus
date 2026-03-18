"""Mail body rendering from corpus yaml body spec."""

from .context import t
from .generators.faker_gen import resolve as faker_resolve


def resolve_value(value, ctx: dict) -> str:
    """
    Resolve a field value — either a plain string (template substitution)
    or a dict with a generation strategy.

    Supported strategies:
      strategy: faker   → delegates to generators.faker_gen.resolve()
    """
    if isinstance(value, dict):
        strategy = value.get("strategy")
        if strategy == "faker":
            return faker_resolve(value)
        raise ValueError(f"Unknown value generation strategy: {strategy!r}")
    return t(value, ctx)


def build_body(body_spec: dict, ctx: dict) -> tuple[str, str]:
    """
    Render a body spec into (contentType, content) ready for Graph API.

    Supports:
      body: null                         → ("text", "")
      body.content: "raw string"         → raw shorthand, no section processing
      body.sections: [...]               → compositional: header / structured / footer
    """
    if body_spec is None:
        return "text", ""

    content_type = body_spec.get("contentType", "text")

    # Raw shorthand
    if "content" in body_spec:
        return content_type, t(body_spec["content"], ctx)

    # Sections
    sections = body_spec.get("sections", [])
    parts = []
    for section in sections:
        stype = section["type"]
        if stype in ("header", "footer"):
            parts.append(t(section["content"], ctx))
        elif stype == "structured":
            parts.append(_render_structured(section, ctx))
        else:
            raise ValueError(f"Unknown body section type: {stype!r}")

    return content_type, "\n".join(parts)


def _render_structured(section: dict, ctx: dict) -> str:
    """Render a structured key-value section using the declared separator."""
    separator = section.get("separator", ": ")
    lines = []
    for field in section.get("fields", []):
        key = t(field["key"], ctx)
        value = resolve_value(field["value"], ctx)
        lines.append(f"{key}{separator}{value}")
    return "\n".join(lines)


def extract_structured_fields(body_spec: dict, ctx: dict) -> dict:
    """
    Return resolved {key: value} pairs from all structured sections.
    Used by manifest builder to populate expected.bodyExtraction source data.
    """
    if not body_spec or "sections" not in body_spec:
        return {}

    separator = ": "
    fields = {}
    for section in body_spec.get("sections", []):
        if section["type"] == "structured":
            separator = section.get("separator", ": ")
            for field in section.get("fields", []):
                fields[t(field["key"], ctx)] = resolve_value(field["value"], ctx)
    return fields


def get_separator(body_spec: dict) -> str:
    """Return the separator declared in the first structured section, or default."""
    if not body_spec or "sections" not in body_spec:
        return ": "
    for section in body_spec.get("sections", []):
        if section["type"] == "structured":
            return section.get("separator", ": ")
    return ": "
