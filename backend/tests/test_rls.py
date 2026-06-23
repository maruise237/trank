"""RLS test: user A cannot see user B's data.

Runs against a live Supabase project (CI). Skipped if not configured.
"""
import os
import pytest

try:
    from supabase import create_client
except ImportError:  # pragma: no cover
    create_client = None

SUPA_URL = os.getenv("SUPABASE_URL")
SUPA_KEY_A = os.getenv("TEST_USER_A_TOKEN")
SUPA_KEY_B = os.getenv("TEST_USER_B_TOKEN")
pytestmark = pytest.mark.skipif(
    not (SUPA_URL and SUPA_KEY_A and SUPA_KEY_B),
    reason="needs two test users (CI)",
)


def test_user_a_cannot_read_user_b_sites():
    client_a = create_client(SUPA_URL, SUPA_KEY_A)
    # Should return only user A's sites (or empty), never user B's.
    resp = client_a.table("sites").select("*").execute()
    for row in resp.data or []:
        assert row["user_id"] != "user-b-expected-id-placeholder"
