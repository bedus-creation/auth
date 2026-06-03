"""Password hashing helpers (bcrypt).

The framework's ``Hash`` facade is unbound (a no-op), so we use bcrypt directly
rather than routing through it.
"""

from typing import Optional

import bcrypt


def make(password: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify(password: str, hashed: Optional[str]) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
