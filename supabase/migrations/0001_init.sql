create extension if not exists "pgcrypto";

create table if not exists profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  email         text not null,
  plan          text not null default 'solo' check (plan in ('solo','builder','agency')),
  trial_ends_at timestamptz,
  is_active     boolean not null default true,
  created_at    timestamptz not null default now()
);

create table if not exists sites (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references profiles(id) on delete cascade,
  domain          text not null,
  name            text not null,
  country_code    char(2) not null,
  location_name   text,
  language_code   char(2) not null,
  is_active       boolean not null default true,
  last_tracked_at timestamptz,
  created_at      timestamptz not null default now()
);

create table if not exists keywords (
  id         uuid primary key default gen_random_uuid(),
  site_id    uuid not null references sites(id) on delete cascade,
  query      text not null,
  status     text not null default 'active' check (status in ('active','paused')),
  created_at timestamptz not null default now()
);

create table if not exists rank_snapshots (
  id                  bigserial primary key,
  keyword_id          uuid not null references keywords(id) on delete cascade,
  checked_at          timestamptz not null,
  position            smallint check (position is null or (position between 1 and 100)),
  url                 text,
  search_volume       integer,
  serp_features       text[],
  delta_vs_yesterday  smallint,
  is_new              boolean not null default false,
  unique (keyword_id, checked_at)
);

create table if not exists admin_actions (
  id          bigserial primary key,
  admin_user  text not null,
  action      text not null,
  target      text,
  metadata    jsonb,
  ip          text,
  user_agent  text,
  created_at  timestamptz not null default now()
);
