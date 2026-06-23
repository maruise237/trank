"""Domain matching + delta computation (pure functions, no IO)."""
from urllib.parse import urlparse


def normalise_domain(value: str) -> str:
    """Strip scheme, path, leading 'www.', lowercase the host."""
    if "://" not in value:
        value = "http://" + value
    host = urlparse(value).hostname or ""
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def _host_of(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def match_domain_in_serp(serp: list[dict], site_domain: str) -> dict | None:
    """
    Return the first (highest-ranking) organic result whose host equals
    or ends with '.' + site_domain. Best position wins because SERP is
    ordered by ascending position.
    """
    target = normalise_domain(site_domain)
    for result in sorted(serp, key=lambda r: r["position"]):
        host = _host_of(result["url"])
        if host == target or host.endswith("." + target):
            return result
    return None


def compute_delta(today_position: int | None, yesterday_position: int | None) -> int | None:
    """Negative = improved (gained positions); None when no history."""
    if today_position is None or yesterday_position is None:
        return None
    return today_position - yesterday_position
