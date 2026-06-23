"""Nightly tracking: fetch SERP -> match domain -> compute delta -> insert snapshots."""
from datetime import datetime, timezone
from celery import shared_task
from app.db import get_service_client
from app.services.positions import match_domain_in_serp, compute_delta
from app.services.dataforseo import DataForSeoClient


def _load_site(db, site_id: str) -> dict | None:
    resp = (
        db.table("sites").select("*").eq("id", site_id).eq("is_active", True).execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def _load_keywords(db, site_id: str) -> list[dict]:
    resp = (
        db.table("keywords").select("*")
        .eq("site_id", site_id).eq("status", "active").execute()
    )
    return resp.data or []


def _load_previous_positions(db, keyword_ids: list[str]) -> dict:
    """{keyword_id: {position, ...}} -- most recent prior snapshot per keyword."""
    if not keyword_ids:
        return {}
    out: dict = {}
    for kid in keyword_ids:
        resp = (
            db.table("rank_snapshots").select("keyword_id, position, checked_at")
            .eq("keyword_id", kid).order("checked_at", desc=True).limit(1).execute()
        )
        rows = resp.data or []
        if rows:
            out[kid] = rows[0]
    return out


@shared_task(name="worker.tasks.track_site.track_site", autoretry_for=(Exception,),
             retry_backoff=True, retry_backoff_max=900, max_retries=3)
def track_site(site_id: str) -> dict:
    db = get_service_client()
    site = _load_site(db, site_id)
    if not site:
        return {"site_id": site_id, "snapshots_written": 0, "reason": "not_found_or_inactive"}

    keywords = _load_keywords(db, site_id)
    if not keywords:
        return {"site_id": site_id, "snapshots_written": 0, "reason": "no_active_keywords"}

    keyword_ids = [k["id"] for k in keywords]
    previous = _load_previous_positions(db, keyword_ids)

    dfs = DataForSeoClient()
    serp = dfs.fetch_serp(
        keywords=[k["query"] for k in keywords],
        country_code=site["country_code"],
        language_code=site["language_code"],
        location_name=site.get("location_name"),
    )

    now = datetime.now(timezone.utc)
    rows = []
    for kw in keywords:
        results = serp.get(kw["query"], [])
        match = match_domain_in_serp(results, site["domain"])
        prev = previous.get(kw["id"])
        prev_pos = prev["position"] if prev else None
        delta = compute_delta(
            today_position=match["position"] if match else None,
            yesterday_position=prev_pos,
        )
        rows.append({
            "keyword_id": kw["id"],
            "checked_at": now.isoformat(),
            "position": match["position"] if match else None,
            "url": match["url"] if match else None,
            "search_volume": match["search_volume"] if match else None,
            "serp_features": match["serp_features"] if match else [],
            "delta_vs_yesterday": delta,
            "is_new": prev is None and match is not None,
        })

    db.table("rank_snapshots").insert(rows).execute()
    db.table("sites").update({"last_tracked_at": now.isoformat()}).eq("id", site_id).execute()

    return {"site_id": site_id, "snapshots_written": len(rows)}


@shared_task(name="worker.tasks.track_site.track_all_sites")
def track_all_sites() -> dict:
    db = get_service_client()
    resp = db.table("sites").select("id").eq("is_active", True).execute()
    for row in resp.data or []:
        track_site.delay(row["id"])
    return {"enqueued": len(resp.data or [])}


@shared_task(name="worker.tasks.track_site.health_check")
def health_check() -> dict:
    return {"ok": True}
