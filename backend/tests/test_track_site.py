from unittest.mock import MagicMock, patch
from worker.tasks.track_site import track_site


def _make_site(domain="monsite.com"):
    return {
        "id": "s1", "user_id": "u1", "domain": domain,
        "name": "Demo", "country_code": "FR", "language_code": "fr",
        "location_name": None, "is_active": True,
    }


def _make_keywords():
    return [{"id": "k1", "query": "ratatouille", "site_id": "s1", "status": "active"}]


def _make_serp(position=5):
    return {"ratatouille": [
        {"position": position, "url": "https://monsite.com/rat",
         "search_volume": 1000, "serp_features": []}
    ]}


def test_track_site_writes_snapshots_and_marks_new():
    """First run ever -> is_new=True, delta=None."""
    serp = _make_serp(position=5)
    db = MagicMock()
    with patch("worker.tasks.track_site._load_site", return_value=_make_site()), \
         patch("worker.tasks.track_site._load_keywords", return_value=_make_keywords()), \
         patch("worker.tasks.track_site._load_previous_positions", return_value={}), \
         patch("worker.tasks.track_site.get_service_client", return_value=db), \
         patch("worker.tasks.track_site.DataForSeoClient") as MockDFS:
        MockDFS.return_value.fetch_serp.return_value = serp
        result = track_site("s1")

    assert result["snapshots_written"] == 1
    insert_call = db.table.return_value.insert.call_args
    payload = insert_call.kwargs.get("rows", insert_call.args[0])
    assert payload[0]["is_new"] is True
    assert payload[0]["position"] == 5
    assert payload[0]["delta_vs_yesterday"] is None


def test_track_site_computes_delta_when_previous_exists():
    """Second run -> delta computed (position 10 -> 7 = gained 3 -> delta -3)."""
    serp = _make_serp(position=7)
    db = MagicMock()
    with patch("worker.tasks.track_site._load_site", return_value=_make_site()), \
         patch("worker.tasks.track_site._load_keywords", return_value=_make_keywords()), \
         patch("worker.tasks.track_site._load_previous_positions",
               return_value={"k1": {"position": 10, "keyword_id": "k1"}}), \
         patch("worker.tasks.track_site.get_service_client", return_value=db), \
         patch("worker.tasks.track_site.DataForSeoClient") as MockDFS:
        MockDFS.return_value.fetch_serp.return_value = serp
        result = track_site("s1")

    assert result["snapshots_written"] == 1
    payload = db.table.return_value.insert.call_args.kwargs.get("rows",
                db.table.return_value.insert.call_args.args[0])
    assert payload[0]["delta_vs_yesterday"] == -3
    assert payload[0]["is_new"] is False


def test_track_site_skips_inactive_site():
    with patch("worker.tasks.track_site._load_site", return_value=None), \
         patch("worker.tasks.track_site.DataForSeoClient") as MockDFS:
        result = track_site("dead-site-id")
    assert result["snapshots_written"] == 0
    assert result["reason"] == "not_found_or_inactive"
    MockDFS.return_value.fetch_serp.assert_not_called()
