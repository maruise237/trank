import vcr
from app.services.dataforseo import DataForSeoClient
from app.config import get_settings


@vcr.use_cassette("tests/cassettes/dfs_serp_success.yaml")
def test_fetch_serp_returns_normalised_results(monkeypatch):
    monkeypatch.setenv("DATAFORSEO_LOGIN", "test@login")
    monkeypatch.setenv("DATAFORSEO_PASSWORD", "pwd")
    monkeypatch.setenv("SUPABASE_URL", "http://x")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "x")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "x")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "x")
    get_settings.cache_clear()
    client = DataForSeoClient()
    results = client.fetch_serp(
        keywords=["ratatouille recipe"],
        country_code="FR",
        language_code="fr",
        location_name=None,
    )
    assert len(results) == 1
    single = results["ratatouille recipe"]
    assert isinstance(single, list)
    assert single[0]["position"] >= 1
    assert "url" in single[0]
