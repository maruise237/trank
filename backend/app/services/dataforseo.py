"""DataForSEO batch SERP client. 0.0006$ per keyword; batch up to 100."""
import base64
import httpx
from ..config import get_settings


class DataForSeoClient:
    def __init__(self) -> None:
        _s = get_settings()
        token = base64.b64encode(f"{_s.dataforseo_login}:{_s.dataforseo_password}".encode()).decode()
        self._headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
        self._url = f"{_s.dataforseo_api_url}/serp/google/organic/live/advanced"
        self._country_map = {"FR": 1023289, "US": 2840, "GB": 2826}

    def fetch_serp(
        self,
        keywords: list[str],
        country_code: str,
        language_code: str,
        location_name: str | None,
    ) -> dict[str, list[dict]]:
        """Returns {keyword: [{position, url, search_volume, serp_features}, ...]}."""
        location_code = self._country_map.get(country_code, 2840)
        batches = [keywords[i:i + 100] for i in range(0, len(keywords), 100)]
        out: dict[str, list[dict]] = {}
        for batch in batches:
            payload = [{
                "keyword": kw,
                "location_code": location_code,
                "language_code": language_code,
                "depth": 100,
                **({"location_name": location_name} if location_name else {}),
            } for kw in batch]
            resp = httpx.post(self._url, json=payload, headers=self._headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            for task in data.get("tasks", []):
                for result in task.get("result", []):
                    kw = result["keyword"]
                    items = []
                    for it in result.get("items", []):
                        if it.get("type") != "organic":
                            continue
                        items.append({
                            "position": it["rank_absolute"],
                            "url": it["url"],
                            "search_volume": result.get("search_volume"),
                            "serp_features": [],
                        })
                    out[kw] = items
        return out
