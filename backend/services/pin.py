"""PIN hashing utilities using stdlib (no external deps)."""
import hashlib
import os
import hmac


# Format: pbkdf2$iterations$salt_hex$hash_hex
_ITERATIONS = 260000
_HASH_ALGO = "sha256"


def hash_pin(pin: str) -> str:
    """Hash a PIN string using PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(_HASH_ALGO, pin.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_pin(pin: str, stored: str) -> bool:
    """Verify a PIN against a stored hash.

    Supports:
    - pbkdf2$... (current format)
    - $2b$... (legacy bcrypt, if bcrypt is installed)
    - plaintext (legacy, for migration)
    """
    if not stored:
        return False

    if stored.startswith("pbkdf2$"):
        parts = stored.split("$")
        if len(parts) != 4:
            return False
        _, iterations, salt_hex, hash_hex = parts
        dk = hashlib.pbkdf2_hmac(
            _HASH_ALGO,
            pin.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(dk.hex(), hash_hex)

    if stored.startswith("$2"):
        # Legacy bcrypt hash — try importing bcrypt
        try:
            import bcrypt
            return bcrypt.checkpw(pin.encode("utf-8"), stored.encode("utf-8"))
        except ImportError:
            return False

    # Legacy plaintext — caller should re-hash after successful verify
    return hmac.compare_digest(pin, stored)
