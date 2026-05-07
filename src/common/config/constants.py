import ipaddress
import re


# for Validations
# Allowed schemes for a URL shortener
ALLOWED_SCHEMES = {"http", "https"}

# Max URL length (browsers and HTTP specs typically cap at ~2000)
MAX_URL_LENGTH = 2048

# Regex to detect IP-based hostnames (v4)
_IPV4_RE = re.compile(
    r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
)

# Private / reserved IPv4 networks that must never be reached
_PRIVATE_NETWORKS = [
    ipaddress.ip_network(cidr)
    for cidr in (
        "0.0.0.0/8",        # "This" network
        "10.0.0.0/8",       # RFC-1918 private
        "100.64.0.0/10",    # Shared address space (CGNAT)
        "127.0.0.0/8",      # Loopback
        "169.254.0.0/16",   # Link-local (AWS metadata endpoint lives here)
        "172.16.0.0/12",    # RFC-1918 private
        "192.0.0.0/24",     # IETF protocol assignments
        "192.168.0.0/16",   # RFC-1918 private
        "198.18.0.0/15",    # Benchmarking
        "198.51.100.0/24",  # TEST-NET-2 (documentation)
        "203.0.113.0/24",   # TEST-NET-3 (documentation)
        "224.0.0.0/4",      # Multicast
        "240.0.0.0/4",      # Reserved
        "255.255.255.255/32",
    )
]

# Common URL shortener redirect-loop domains (add your own short domain here)
_SHORTENER_DOMAINS: set[str] = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "buff.ly", "short.link", "rb.gy", "tiny.cc", "is.gd",
    # TODO: add your own service hostname to prevent self-loops
}


# For Generation

# ---------------------------------------------------------------------------
# Alphabet design
# ---------------------------------------------------------------------------
# Removed visually ambiguous characters: 0/O, 1/l/I
# This prevents user confusion when reading codes aloud or from print.
_SAFE_ALPHABET = (
    "abcdefghjkmnpqrstuvwxyz"   # lowercase, minus: i, l, o
    "ABCDEFGHJKMNPQRSTUVWXYZ"   # uppercase, minus: I, L, O
    "23456789"                  # digits,    minus: 0, 1
)

# Minimum code length for adequate collision resistance.
# At length 7 with 55 chars: 55^7 ≈ 1.15 billion combinations — reasonable
# for moderate scale. Bump to 8+ for high-traffic services.
_MIN_LENGTH = 6
_DEFAULT_LENGTH = 7
_MAX_LENGTH = 32

# Characters that, when they appear consecutively or in certain patterns,
# can produce offensive or confusing words. We reject codes containing any
# of these substrings (case-insensitive).
_BLOCKED_SUBSTRINGS: frozenset[str] = frozenset(
    {
        # Add your own profanity / brand-conflict list here.
        # Keeping this short to avoid false positives.
        "sex", "ass", "fuk", "fck",
    }
)
