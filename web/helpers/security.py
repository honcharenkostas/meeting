import secrets
from typing import Optional
from passlib.hash import argon2

# ---- CSRF config ----------------------------------------------------
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

# ---- Password hashing -----------------------------------------------
def hash_password(plain: str) -> str:
    """Hash plain text password using Argon2."""
    return argon2.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    try:
        return argon2.verify(plain, hashed)
    except Exception:
        return False

# ---- CSRF token helpers ---------------------------------------------
def new_csrf_token() -> str:
    """Generate a new CSRF token (URL-safe)."""
    return secrets.token_urlsafe(32)

def validate_csrf(cookie_token: Optional[str], header_token: Optional[str]) -> bool:
    """Double-submit cookie pattern check."""
    if not cookie_token or not header_token:
        return False
    return secrets.compare_digest(cookie_token, header_token)
