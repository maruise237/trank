create index if not exists idx_sites_user on sites(user_id);
create index if not exists idx_keywords_site on keywords(site_id);
create index if not exists idx_snapshots_kw_time on rank_snapshots(keyword_id, checked_at desc);

create or replace view latest_snapshots as
select distinct on (k.id)
  k.id as keyword_id,
  k.site_id,
  s.user_id,
  k.query,
  s.domain,
  rs.checked_at,
  rs.position,
  rs.url,
  rs.search_volume,
  rs.serp_features,
  rs.delta_vs_yesterday,
  rs.is_new
from keywords k
join sites s on s.id = k.site_id
left join rank_snapshots rs on rs.keyword_id = k.id
order by k.id, rs.checked_at desc nulls last;
