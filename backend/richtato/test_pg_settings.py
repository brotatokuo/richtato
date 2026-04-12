"""Test settings for PostgreSQL - uses the real DB config with test optimizations."""

from richtato.settings import *  # noqa: F401, F403

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
