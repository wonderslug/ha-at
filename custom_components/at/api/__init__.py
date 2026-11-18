"""
API package for at.

Exception hierarchy:
    AtApiClientError (base)
    ├── AtApiClientCommunicationError (network/timeout)
    │   └── AtApiClientRateLimitError (429, carries retry_after)
    └── AtApiClientAuthenticationError (401/403)

The coordinator maps them onto ConfigEntryAuthFailed and UpdateFailed; nothing else
in the integration imports this package.
"""

from .client import (
    FAN_SPEEDS,
    AtApiClient,
    AtApiClientAuthenticationError,
    AtApiClientCommunicationError,
    AtApiClientError,
    AtApiClientRateLimitError,
)

__all__ = [
    "FAN_SPEEDS",
    "AtApiClient",
    "AtApiClientAuthenticationError",
    "AtApiClientCommunicationError",
    "AtApiClientError",
    "AtApiClientRateLimitError",
]
