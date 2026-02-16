"""PIN hashing utilities using bcrypt."""
import bcrypt


def hash_pin(pin: str) -> str:
    """Hash a PIN string and return the bcrypt hash."""
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, hashed: str) -> bool:
    """Verify a PIN against a bcrypt hash.
    
    Also handles legacy plaintext PINs by detecting non-bcrypt values
    and comparing directly (for migration).
    """
    if not hashed:
        return False
    # Bcrypt hashes start with $2b$ (or $2a$, $2y$)
    if hashed.startswith("$2"):
        return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))
    # Legacy plaintext comparison — caller should re-hash after successful verify
    return pin == hashed
