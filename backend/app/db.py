"""Supabase client factories (user-scoped vs service-role)."""
from supabase import create_client, Client
from .config import get_settings

_settings = get_settings()


def get_service_client() -> Client:
    """Service-role client — bypasses RLS. Admin/internal use ONLY."""
    return create_client(_settings.supabase_url, _settings.supabase_service_role_key)


def get_user_client(access_token: str) -> Client:
    """User-scoped client that applies RLS for the given JWT."""
    client = create_client(_settings.supabase_url, _settings.supabase_anon_key)
    client.auth.set_session(access_token, refresh_token="")
    return client
