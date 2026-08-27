"""NPI / identifier helpers (synthetic only)."""

from __future__ import annotations


def luhn_check_digit(body9: str) -> str:
    """NPI check digit: Luhn on 80840 + 9-digit body."""
    full = "80840" + body9
    total = 0
    reverse = full[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - (total % 10)) % 10)


def make_npi(rng, *, invalid: bool = False) -> str:
    body = "".join(str(rng.integers(0, 10)) for _ in range(9))
    if invalid:
        bad = (int(luhn_check_digit(body)) + 1) % 10
        return body + str(bad)
    return body + luhn_check_digit(body)


def make_dea(rng) -> str:
    letters = "ABFGMPR"
    return f"{letters[int(rng.integers(0, len(letters)))]}{letters[int(rng.integers(0, len(letters)))]}" + "".join(
        str(rng.integers(0, 10)) for _ in range(7)
    )


def make_me(rng) -> str:
    return "".join(str(rng.integers(0, 10)) for _ in range(11))


def make_hin(rng) -> str:
    return "H" + "".join(str(rng.integers(0, 10)) for _ in range(8))
