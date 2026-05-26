"""Per-institution Playwright adapters.

Adapters never touch credentials. They expose three responsibilities:

1. :meth:`BaseInstitutionAdapter.interactive_login` — pop a headed browser
   for the user, wait for sign-in to land on the post-login URL, capture
   ``storage_state``, and best-effort discover bank-side accounts.
2. :meth:`BaseInstitutionAdapter.download_account` — navigate to a stored
   activity URL with the existing ``storage_state`` and download a CSV/XLS.
3. :func:`get_adapter` — registry lookup by institution slug.
"""

from __future__ import annotations

from scripts.bank_sync.institutions.base import BaseInstitutionAdapter
from scripts.bank_sync.institutions.bofa import BofaAdapter
from scripts.bank_sync.institutions.chase import ChaseAdapter
from scripts.bank_sync.institutions.guideline import GuidelineAdapter
from scripts.bank_sync.institutions.robinhood import RobinhoodAdapter

_REGISTRY: dict[str, type[BaseInstitutionAdapter]] = {
    "bofa": BofaAdapter,
    "bank_of_america": BofaAdapter,
    "chase": ChaseAdapter,
    "jpmorgan_chase": ChaseAdapter,
    "guideline": GuidelineAdapter,
    "robinhood": RobinhoodAdapter,
}


def get_adapter(slug: str) -> BaseInstitutionAdapter:
    """Return an instance of the adapter for ``slug``.

    Raises ``KeyError`` for unknown institutions so the agent can surface a
    clear configuration error to the user.
    """

    try:
        cls = _REGISTRY[slug]
    except KeyError as exc:
        raise KeyError(f"No bank-sync adapter for institution slug {slug!r}") from exc
    return cls()
