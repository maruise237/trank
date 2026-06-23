create or replace function enforce_single_site() returns trigger as $$
declare
  cnt integer;
  usr_plan text;
begin
  select plan into usr_plan from profiles where id = new.user_id;
  if usr_plan = 'solo' then
    select count(*) into cnt from sites where user_id = new.user_id;
    if cnt >= 1 then
      raise exception 'Solo plan limited to 1 site';
    end if;
  end if;
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_enforce_single_site on sites;
create trigger trg_enforce_single_site
  before insert on sites
  for each row execute function enforce_single_site();

create or replace function enforce_keyword_cap() returns trigger as $$
declare
  cnt integer;
  usr_plan text;
  site_user uuid;
begin
  select user_id into site_user from sites where id = new.site_id;
  select plan into usr_plan from profiles where id = site_user;
  if usr_plan = 'solo' then
    select count(*) into cnt from keywords k
    join sites s on s.id = k.site_id
    where s.user_id = site_user and k.status = 'active';
    if cnt >= 200 then
      raise exception 'Solo plan limited to 200 active keywords';
    end if;
  end if;
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_enforce_keyword_cap on keywords;
create trigger trg_enforce_keyword_cap
  before insert on keywords
  for each row execute function enforce_keyword_cap();
