"""Faker-based value generation for corpus fixtures.

Values declared in corpus yaml as:
    value:
      strategy: faker
      method: company
      locale: de_DE

are resolved here before being written into the manifest and the message body.
"""

from faker import Faker

_instances: dict[str, Faker] = {}


def _get(locale: str) -> Faker:
    if locale not in _instances:
        _instances[locale] = Faker(locale)
    return _instances[locale]


def resolve(spec: dict) -> str:
    """
    Resolve a faker value spec to a string.

    spec:
      strategy: faker
      method: company        # any Faker attribute
      locale: de_DE          # optional, defaults to en_US
      seed: 42               # optional, for reproducibility
    """
    locale = spec.get("locale", "en_US")
    method = spec["method"]
    seed   = spec.get("seed")

    faker = _get(locale)
    if seed is not None:
        Faker.seed(seed)

    value = getattr(faker, method)
    return value() if callable(value) else str(value)
