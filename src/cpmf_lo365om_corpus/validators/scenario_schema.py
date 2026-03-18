"""JSON Schema definition for corpus scenario yaml files."""

SCENARIO_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12",
    "type": "object",
    "required": ["scenario", "fixtures"],
    "additionalProperties": True,
    "properties": {

        "scenario": {
            "type": "object",
            "required": ["name", "workload"],
            "properties": {
                "name":     {"type": "string", "minLength": 1},
                "workload": {"type": "string", "enum": ["mail", "files"]},
            },
        },

        "fixtures": {
            "type": "object",
            "properties": {
                "mail": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["label", "subject"],
                        "properties": {
                            "label":   {"type": "string", "minLength": 1,
                                        "pattern": "^[A-Z][A-Z0-9_]*$"},
                            "subject": {"type": "string", "minLength": 1},
                            "body":    {
                                "oneOf": [
                                    {"type": "null"},
                                    {
                                        "type": "object",
                                        "properties": {
                                            "contentType": {"type": "string",
                                                            "enum": ["text", "html"]},
                                            "content":  {"type": "string"},
                                            "sections": {"type": "array"},
                                        },
                                    },
                                ]
                            },
                            "attachments": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["strategy", "name"],
                                    "properties": {
                                        "strategy": {
                                            "type": "string",
                                            "enum": ["generate_text", "generate_pdf",
                                                     "generate_xlsx", "random_bytes",
                                                     "fixture_file"],
                                        },
                                        "name": {
                                            "oneOf": [
                                                {"type": "string", "minLength": 1},
                                                {
                                                    "type": "object",
                                                    "required": ["strategy"],
                                                    "properties": {
                                                        "strategy": {"type": "string"},
                                                        "case":     {"type": "string"},
                                                    },
                                                },
                                            ]
                                        },
                                    },
                                },
                            },
                            "importance": {"type": "string",
                                           "enum": ["low", "normal", "high"]},
                            "isRead":     {"type": "boolean"},
                        },
                    },
                },
                "files": {"type": "array"},
            },
        },

        "expected":  {"type": "object"},
        "execution": {"type": "object"},
        "tests":     {"type": "array", "items": {"type": "string"}},
    },
}
