"""Airport and supported metropolitan-area code resolution."""

from fli.models import Airport

AIRPORT_GROUPS = {"NYC": ("JFK", "LGA", "EWR")}


def resolve_airports(code: str) -> list[Airport]:
    code = code.strip().upper()
    codes = AIRPORT_GROUPS.get(code, (code,))
    try:
        return [Airport[c] for c in codes]
    except KeyError as exc:
        raise ValueError(f"Unknown airport or city code: {code}") from exc
