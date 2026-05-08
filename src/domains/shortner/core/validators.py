import ipaddress
import re
import anyio.to_thread
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

from src.common.config.settings import get_settings
from src.common.config.constants import (
    ALLOWED_SCHEMES,
    MAX_URL_LENGTH,
    _PRIVATE_NETWORKS,
    _SHORTENER_DOMAINS,
)

settings = get_settings()



@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str | None = None  # Human-readable rejection reason

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(valid=True)

    @classmethod
    def fail(cls, reason: str) -> "ValidationResult":
        return cls(valid=False, reason=reason)


# ---------------------------------------------------------------------------
# Individual checks (each returns ValidationResult)
# ---------------------------------------------------------------------------

def _check_length(url: str) -> ValidationResult:
    if not url or not url.strip():
        return ValidationResult.fail("URL must not be empty.")
    if len(url) > MAX_URL_LENGTH:
        return ValidationResult.fail(
            f"URL exceeds maximum allowed length of {MAX_URL_LENGTH} characters."
        )
    return ValidationResult.ok()


def _check_scheme(parsed) -> ValidationResult:
    if parsed.scheme not in ALLOWED_SCHEMES:
        return ValidationResult.fail(
            f"URL scheme '{parsed.scheme}' is not allowed. "
            f"Only {sorted(ALLOWED_SCHEMES)} are accepted."
        )
    return ValidationResult.ok()


def _check_has_hostname(parsed) -> ValidationResult:
    if not parsed.hostname:
        return ValidationResult.fail("URL does not contain a valid hostname.")
    return ValidationResult.ok()


def _check_no_credentials(parsed) -> ValidationResult:
    """Reject URLs that embed username / password (potential phishing vector)."""
    if parsed.username or parsed.password:
        return ValidationResult.fail(
            "URLs with embedded credentials (user:pass@host) are not allowed."
        )
    return ValidationResult.ok()


def _check_blocked_domains(parsed, blocked_domains: set[str]) -> ValidationResult:
    hostname = parsed.hostname.lower()
    # Exact match or any parent domain match
    # e.g. blocked = "evil.com" also blocks "sub.evil.com"
    for blocked in blocked_domains:
        if hostname == blocked or hostname.endswith(f".{blocked}"):
            return ValidationResult.fail(
                f"The domain '{hostname}' is on the blocked list."
            )
    return ValidationResult.ok()


def _check_no_shortener_loop(parsed) -> ValidationResult:
    hostname = parsed.hostname.lower()
    for shortener in _SHORTENER_DOMAINS:
        if hostname == shortener or hostname.endswith(f".{shortener}"):
            return ValidationResult.fail(
                f"Chaining through another URL shortener ('{hostname}') is not allowed."
            )
    return ValidationResult.ok()


def _check_not_ip_address(parsed) -> ValidationResult:
    """
    Block raw IP addresses in the host to prevent SSRF via numeric IPs.
    IPv6 literals are always rejected; IPv4 only if private/reserved.
    """
    hostname = parsed.hostname

    # IPv6 literals arrive without brackets after urlparse
    # urlparse strips brackets, so a pure hex/colon string = IPv6
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        return ValidationResult.ok()  # It's a domain name — fine

    if isinstance(addr, ipaddress.IPv6Address):
        if addr.is_loopback or addr.is_private or addr.is_link_local or addr.is_unspecified:
            return ValidationResult.fail(
                f"IPv6 address '{hostname}' resolves to a private/reserved range."
            )
        return ValidationResult.ok()

    # IPv4
    for network in _PRIVATE_NETWORKS:
        if addr in network:
            return ValidationResult.fail(
                f"IP address '{hostname}' is in a private/reserved range ({network}) "
                "and cannot be used as a shortener target."
            )
    return ValidationResult.ok()


def _check_dns_resolves(parsed) -> ValidationResult:
    """
    Resolve the hostname and verify none of the returned IPs are private.
    This guards against DNS rebinding and internal-hostname SSRF.
    """
    hostname = parsed.hostname
    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return ValidationResult.fail(
            f"Hostname '{hostname}' could not be resolved. "
            "Please check the URL and try again."
        )

    for _family, _type, _proto, _canonname, sockaddr in results:
        ip_str = sockaddr[0]
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        for network in _PRIVATE_NETWORKS:
            if addr in network:
                return ValidationResult.fail(
                    f"Hostname '{hostname}' resolves to a private/reserved IP "
                    f"({ip_str}) and cannot be used as a shortener target."
                )

    return ValidationResult.ok()


def _check_no_suspicious_patterns(url: str) -> ValidationResult:
    """Catch common obfuscation / injection patterns."""
    lower = url.lower()

    # Null bytes
    if "\x00" in url:
        return ValidationResult.fail("URL contains a null byte.")

    # Unicode direction-override characters (homograph / spoofing attacks)
    for char in ("\u202e", "\u200b", "\u2028", "\u2029", "\ufeff"):
        if char in url:
            return ValidationResult.fail(
                "URL contains disallowed Unicode control characters."
            )

    # Data URIs that somehow slipped past scheme check
    if lower.startswith("data:"):
        return ValidationResult.fail("Data URIs are not allowed.")

    # JavaScript injection
    if re.search(r"javascript\s*:", lower):
        return ValidationResult.fail("JavaScript URIs are not allowed.")

    # Excessively nested path (path traversal indicator)
    if url.count("../") > 3 or url.count("..\\") > 3:
        return ValidationResult.fail("URL contains excessive path-traversal sequences.")

    return ValidationResult.ok()


def _check_port(parsed) -> ValidationResult:
    """Only allow standard ports (80/443) or no explicit port."""
    port = parsed.port
    if port is None:
        return ValidationResult.ok()
    allowed_ports = {80, 443}
    if port not in allowed_ports:
        return ValidationResult.fail(
            f"Port {port} is not allowed. Only ports 80 and 443 are accepted."
        )
    return ValidationResult.ok()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def validate_url(url: str, *, resolve_dns: bool = True) -> ValidationResult:
    """
    Run all validation checks against *url* and return a ValidationResult.

    Args:
        url:         The raw URL string submitted by the user.
        resolve_dns: When True (default), perform a live DNS lookup to guard
                     against SSRF via internal hostnames.  Set to False in
                     unit-tests or offline environments.

    Returns:
        ValidationResult(valid=True) on success, or
        ValidationResult(valid=False, reason="…") on the first failing check.
    """
    # Ordered pipeline — fail fast on cheap checks before expensive ones
    checks = [
        lambda: _check_length(url),
        lambda: _check_no_suspicious_patterns(url),  # before parse, catches null bytes etc.
        lambda: _check_scheme(parsed := urlparse(url)) or parsed,  # parse once
    ]

    # --- length + suspicious patterns (pre-parse) ---
    for check_fn in (_check_length, _check_no_suspicious_patterns):
        result = check_fn(url)
        if not result.valid:
            return result

    # --- parse once, then run structural checks ---
    parsed = urlparse(url)

    structural_checks = [
        _check_scheme(parsed),
        _check_has_hostname(parsed),
        _check_no_credentials(parsed),
        _check_port(parsed),
        _check_not_ip_address(parsed),
        _check_blocked_domains(parsed, set(settings.blocked_domains)),
        _check_no_shortener_loop(parsed),
    ]

    for result in structural_checks:
        if not result.valid:
            return result

    # --- network check (optional, most expensive) ---
    if resolve_dns:
        # Run blocking DNS lookup in a thread pool to avoid starving the event loop
        result = await anyio.to_thread.run_sync(_check_dns_resolves, parsed)
        if not result.valid:
            return result

    return ValidationResult.ok()


# Convenience wrapper that matches the original boolean signature
async def validate_url_security(url: str) -> bool:
    """Drop-in replacement for the original function (returns bool)."""
    return (await validate_url(url)).valid