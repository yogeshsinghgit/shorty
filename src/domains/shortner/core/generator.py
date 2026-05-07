import secrets
from typing import Container

from src.common.config.constants import (
    _BLOCKED_SUBSTRINGS,
    _DEFAULT_LENGTH,
    _MAX_LENGTH,
    _MIN_LENGTH,
    _SAFE_ALPHABET,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_clean(code: str) -> bool:
    """Return True if *code* contains no blocked substrings."""
    lower = code.lower()
    return not any(sub in lower for sub in _BLOCKED_SUBSTRINGS)


def _entropy_bits(alphabet_size: int, length: int) -> float:
    """Return the theoretical entropy in bits for the given parameters."""
    from math import log2
    return log2(alphabet_size) * length


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_short_code(
    length: int = _DEFAULT_LENGTH,
    *,
    alphabet: str = _SAFE_ALPHABET,
    existing_codes: Container[str] | None = None,
    max_attempts: int = 10,
) -> str:
    """
    Generate a cryptographically secure, URL-safe short code.

    Args:
        length:         Number of characters in the code (default 7).
        alphabet:       Character pool to draw from. Defaults to the
                        visually-unambiguous safe alphabet.
        existing_codes: Optional set / Bloom-filter-like container that
                        supports ``in`` checks. When provided, the generator
                        will retry on collision up to *max_attempts* times.
                        For very high fill-rates, increase *length* instead.
        max_attempts:   Maximum retries before raising RuntimeError.

    Returns:
        A unique, clean short code string.

    Raises:
        ValueError:     If *length* or *alphabet* are outside safe bounds.
        RuntimeError:   If a non-colliding code cannot be found within
                        *max_attempts* (signals the keyspace is nearly full).
    """
    # --- validate inputs ---
    if not (_MIN_LENGTH <= length <= _MAX_LENGTH):
        raise ValueError(
            f"length must be between {_MIN_LENGTH} and {_MAX_LENGTH}, got {length}."
        )

    unique_chars = len(set(alphabet))
    if unique_chars < 10:
        raise ValueError(
            f"alphabet must contain at least 10 distinct characters, got {unique_chars}."
        )

    bits = _entropy_bits(unique_chars, length)
    if bits < 30:
        raise ValueError(
            f"Insufficient entropy ({bits:.1f} bits). "
            "Increase length or alphabet size."
        )

    # --- generation loop ---
    for attempt in range(1, max_attempts + 1):
        code = "".join(secrets.choice(alphabet) for _ in range(length))

        if not _is_clean(code):
            continue  # regenerate — no penalty, just spin again

        if existing_codes is not None and code in existing_codes:
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Could not generate a unique short code after {max_attempts} "
                    "attempts. Consider increasing code length or clearing stale codes."
                )
            continue

        return code

    # Should be unreachable, but satisfies type checkers.
    raise RuntimeError("Short code generation failed unexpectedly.")


def validate_custom_code(code: str, *, alphabet: str = _SAFE_ALPHABET) -> str:
    """
    Validate and normalise a user-supplied vanity / custom short code.

    Args:
        code:     The raw string submitted by the user.
        alphabet: Allowed character set.

    Returns:
        The validated code (stripped).

    Raises:
        ValueError: With a user-friendly message describing the problem.
    """
    code = code.strip()

    if not (_MIN_LENGTH <= len(code) <= _MAX_LENGTH):
        raise ValueError(
            f"Custom code must be between {_MIN_LENGTH} and {_MAX_LENGTH} characters long."
        )

    allowed = set(alphabet)
    bad_chars = sorted({c for c in code if c not in allowed})
    if bad_chars:
        raise ValueError(
            f"Custom code contains disallowed characters: {bad_chars}. "
            "Use only letters and digits (ambiguous characters like 0, O, 1, l are excluded)."
        )

    if not _is_clean(code):
        raise ValueError("Custom code contains a disallowed word or pattern.")

    return code