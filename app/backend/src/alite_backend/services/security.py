# alite_backend/core/security.py

import logging
from typing import Any, Optional, Dict
import bcrypt
from datetime import datetime, timedelta, timezone
import jwt
from alite_backend.config import settings

logger = logging.getLogger(__name__)

# enforce explicit algorithm declaration
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
BCRYPT_ROUNDS = 12

# initialize CryptContext specifying bcrypt as the primary scheme
# 'deprecated="auto"' automatically marks older hashes for re-hashing if you upgrade schemes later.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Generates a salted, C-accelerated bcrypt hash from a plain-text password string.

    Args:
        password (str): Raw plain-text password submitted by user or seed script.

    Returns:
        str: Salted bcrypt hash formatted as a UTF-8 string for DB storage.
    """
    # convert the plain-text password string to raw UTF-8 bytes
    password_bytes: bytes = password.encode("utf-8")

    # generate a random salt with the configured work factor
    salt: bytes = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)

    # hash the password bytes against the generated salt
    hashed_bytes: bytes = bcrypt.hashpw(password_bytes, salt)

    # decode the byte string back to UTF-8 for database column persistence
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Cryptographically verifies a candidate plain-text password against a stored bcrypt hash.

    Args:
        plain_password (str): Raw candidate password from login attempt.
        hashed_password (str): Stored bcrypt hash string retrieved from PostgreSQL.

    Returns:
        bool: True if candidate matches the hash; False otherwise.
    """
    try:
        # encode both inputs into bytes required by C-bindings
        plain_bytes: bytes = plain_password.encode("utf-8")
        hashed_bytes: bytes = hashed_password.encode("utf-8")

        # perform constant-time comparison to prevent timing attacks
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as exc:
        logger.error("Password verification error: %s", exc)
        return False


def create_access_token(
    subject: str | Any, role: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a cryptographically signed JWT access token using HS256.

    Args:
        subject: Unique identifier for the user (e.g., user.id or username).
        role: Enum or string representing the user's RBAC role (e.g., 'student', 'instructor').
        expires_delta: Custom token lifetime; defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        str: Encoded, signed JWT string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # construct standard claims payload (RFC 7519)
    payload: Dict[str, Any] = {
        "sub": str(subject),  # Subject identifier
        "role": role,  # Application-specific RBAC claim
        "iat": now,  # Issued-at timestamp
        "exp": expire,  # Expiration timestamp
        "type": "access_token",  # Token type identifier
    }

    # encode and sign using the symmetric SECRET_KEY and HS256
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and verifies an incoming JWT token against backend criteria.

    Args:
        token: Raw JWT string from the 'Authorization: Bearer <token>' header.

    Returns:
        Optional[Dict[str, Any]]: Unpacked payload dictionary if valid; None if verification fails.
    """
    try:
        # Security Critical: Always pass explicit 'algorithms' list to decode()
        # to prevent Algorithm Confusion / Key Substitution Attacks.
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["sub", "exp", "role"],  # Reject tokens missing core claims
            },
        )
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT verification failed: Token has expired.")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("JWT verification failed: Invalid token (%s)", str(exc))
        return None
