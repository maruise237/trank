from app.services.positions import normalise_domain, match_domain_in_serp, compute_delta


def test_normalise_domain_strips_scheme_and_www():
    assert normalise_domain("https://www.monsite.com") == "monsite.com"
    assert normalise_domain("http://monsite.com/") == "monsite.com"
    assert normalise_domain("MONSITE.COM") == "monsite.com"
    assert normalise_domain("monsite.com/some/path") == "monsite.com"


def test_match_domain_in_serp_returns_best_position():
    serp = [
        {"position": 1, "url": "https://competitor.com/a"},
        {"position": 2, "url": "https://www.monsite.com/article"},
        {"position": 5, "url": "https://sub.monsite.com/x"},
        {"position": 8, "url": "https://monsite.com/other"},
    ]
    result = match_domain_in_serp(serp, "monsite.com")
    assert result["position"] == 2
    assert result["url"] == "https://www.monsite.com/article"


def test_match_domain_in_serp_returns_none_when_absent():
    serp = [{"position": 1, "url": "https://other.com"}]
    assert match_domain_in_serp(serp, "monsite.com") is None


def test_compute_delta_when_previous_exists():
    assert compute_delta(today_position=7, yesterday_position=10) == -3


def test_compute_delta_when_no_previous():
    assert compute_delta(today_position=12, yesterday_position=None) is None
