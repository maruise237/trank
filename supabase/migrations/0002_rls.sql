alter table sites enable row level security;
alter table keywords enable row level security;
alter table rank_snapshots enable row level security;
alter table profiles enable row level security;
alter table admin_actions enable row level security;

create policy "profiles_select_own" on profiles
  for select using (auth.uid() = id);
create policy "profiles_update_own" on profiles
  for update using (auth.uid() = id);
create policy "profiles_insert_own" on profiles
  for insert with check (auth.uid() = id);

create policy "sites_owner_all" on sites
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "keywords_owner_all" on keywords
  for all using (
    exists (select 1 from sites s where s.id = keywords.site_id and s.user_id = auth.uid())
  ) with check (
    exists (select 1 from sites s where s.id = keywords.site_id and s.user_id = auth.uid())
  );

create policy "snapshots_owner_select" on rank_snapshots
  for select using (
    exists (
      select 1 from keywords k
      join sites s on s.id = k.site_id
      where k.id = rank_snapshots.keyword_id and s.user_id = auth.uid()
    )
  );

create policy "admin_actions_none" on admin_actions
  for all using (false) with check (false);
