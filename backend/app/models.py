"""Pydantic models mirroring the DB schema (used by services + API)."""
from datetime import datetime
from pydantic import BaseModel, Field


class Site(BaseModel):
    id: str
    user_id: str
    domain: str
    name: str
    country_code: str
    location_name: str | None = None
    language_code: str
    is_active: bool = True
    last_tracked_at: datetime | None = None
    created_at: datetime | None = None


class Keyword(BaseModel):
    id: str
    site_id: str
    query: str
    status: str = "active"
    created_at: datetime | None = None


class Snapshot(BaseModel):
    keyword_id: str
    checked_at: datetime
    position: int | None = None
    url: str | None = None
    search_volume: int | None = None
    serp_features: list[str] = Field(default_factory=list)
    delta_vs_yesterday: int | None = None
    is_new: bool = False


class SerpResult(BaseModel):
    """One organic result returned by DataForSEO, normalised."""
    position: int
    url: str
    search_volume: int | None = None
    serp_features: list[str] = Field(default_factory=list)


class KeywordPosition(BaseModel):
    """Output of matching a site domain against a SERP."""
    keyword_query: str
    position: int | None
    url: str | None
    search_volume: int | None
    serp_features: list[str]
    delta_vs_yesterday: int | None
    is_new: bool
