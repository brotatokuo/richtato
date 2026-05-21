"""Per-institution adapter modules.

Use :func:`get_adapter` to resolve a slug to its adapter class without
hard-coded if/else chains in the runner.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.automation.institutions.base import InstitutionAdapter


def get_adapter(slug: str) -> "InstitutionAdapter":
    """Return an adapter instance for ``slug``.

    Imports happen lazily so a single broken adapter module does not crash the
    whole runner at import time.
    """

    from importlib import import_module

    from scripts.automation.institutions.base import InstitutionAdapter

    module_name = f"scripts.automation.institutions.{slug}"
    module = import_module(module_name)
    adapter_cls = getattr(module, "Adapter", None)
    if adapter_cls is None:
        raise LookupError(f"Adapter class missing in {module_name}")
    if not issubclass(adapter_cls, InstitutionAdapter):
        raise TypeError(f"{module_name}.Adapter must subclass InstitutionAdapter")
    return adapter_cls()
