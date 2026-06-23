"""Verify the 1-site + 200-KW solo triggers fire.

These run against a Supabase project with migrations applied (CI env).
Skipped if SUPABASE_URL not configured for tests.
"""
import os
import pytest

try:
    from supabase import create_client
except ImportError:  # pragma: no cover
    create_client = None

SUPA_URL = os.getenv("SUPABASE_URL")
SUPA_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
pytestmark = pytest.mark.skipif(
    not (SUPA_URL and SUPA_KEY),
    reason="needs live Supabase test project (CI)",
)


@pytest.fixture
def db():
    return create_client(SUPA_URL, SUPA_KEY)


def test_second_site_for_solo_user_is_rejected(db):
    """Solo plan: inserting a 2nd site must raise."""
    with pytest.raises(Exception, match="Solo plan limited to 1 site"):
        db.table("sites").insert({
            "user_id": "00000000-0000-0000-0000-000000000001",
            "domain": "second.com", "name": "Second",
            "country_code": "FR", "language_code": "fr",
        }).execute()
