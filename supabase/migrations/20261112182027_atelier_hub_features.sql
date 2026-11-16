
create table if not exists public.article_collections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 2 and 40),
  created_at timestamptz not null default now(),
  unique (id, user_id),
  unique (user_id, name)
);
create table if not exists public.article_collection_items (
  collection_id uuid not null,
  user_id uuid not null references auth.users(id) on delete cascade,
  article_id text not null,
  title text not null,
  category text,
  url text,
  image text,
  added_at timestamptz not null default now(),
  primary key (collection_id, article_id),
  foreign key (collection_id, user_id) references public.article_collections(id, user_id) on delete cascade
);
create table if not exists public.article_suggestions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 8 and 180),
  url text not null check (url ~ '^https?://'),
  note text check (char_length(coalesce(note,'')) <= 1000),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  created_at timestamptz not null default now(),
  reviewed_at timestamptz,
  reviewed_by uuid references auth.users(id) on delete set null
);
create table if not exists public.atelier_polls (
  id uuid primary key default gen_random_uuid(),
  question text not null check (char_length(question) between 8 and 180),
  options jsonb not null check (jsonb_typeof(options) = 'array' and jsonb_array_length(options) between 2 and 6),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  created_by uuid references auth.users(id) on delete set null
);
create table if not exists public.atelier_poll_votes (
  poll_id uuid not null references public.atelier_polls(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  option_index smallint not null check (option_index between 0 and 5),
  voted_at timestamptz not null default now(),
  primary key (poll_id, user_id)
);
create table if not exists public.atelier_poll_results (
  poll_id uuid not null references public.atelier_polls(id) on delete cascade,
  option_index smallint not null check (option_index between 0 and 5),
  vote_count bigint not null default 0 check (vote_count >= 0),
  primary key (poll_id, option_index)
);
create table if not exists public.editorial_picks (
  article_id text primary key,
  title text not null,
  category text,
  excerpt text,
  source text,
  url text,
  image text,
  note text not null check (char_length(note) between 10 and 500),
  position integer not null default 0,
  active boolean not null default true,
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id) on delete set null
);
alter table public.article_collections enable row level security;
alter table public.article_collection_items enable row level security;
alter table public.article_suggestions enable row level security;
alter table public.atelier_polls enable row level security;
alter table public.atelier_poll_votes enable row level security;
alter table public.atelier_poll_results enable row level security;
alter table public.editorial_picks enable row level security;

drop policy if exists collections_own_select on public.article_collections;
create policy collections_own_select on public.article_collections for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists collections_own_insert on public.article_collections;
create policy collections_own_insert on public.article_collections for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists collections_own_update on public.article_collections;
create policy collections_own_update on public.article_collections for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists collections_own_delete on public.article_collections;
create policy collections_own_delete on public.article_collections for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists collection_items_own_select on public.article_collection_items;
create policy collection_items_own_select on public.article_collection_items for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists collection_items_own_insert on public.article_collection_items;
create policy collection_items_own_insert on public.article_collection_items for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists collection_items_own_delete on public.article_collection_items;
create policy collection_items_own_delete on public.article_collection_items for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists suggestions_own_select on public.article_suggestions;
create policy suggestions_own_select on public.article_suggestions for select to authenticated using ((select auth.uid()) = user_id or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists suggestions_own_insert on public.article_suggestions;
create policy suggestions_own_insert on public.article_suggestions for insert to authenticated with check ((select auth.uid()) = user_id and status = 'pending');
drop policy if exists suggestions_admin_update on public.article_suggestions;
create policy suggestions_admin_update on public.article_suggestions for update to authenticated using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin') with check ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

drop policy if exists polls_public_read on public.atelier_polls;
create policy polls_public_read on public.atelier_polls for select to anon, authenticated using (active = true or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists polls_admin_insert on public.atelier_polls;
create policy polls_admin_insert on public.atelier_polls for insert to authenticated with check ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists polls_admin_update on public.atelier_polls;
create policy polls_admin_update on public.atelier_polls for update to authenticated using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin') with check ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

drop policy if exists poll_votes_own_select on public.atelier_poll_votes;
create policy poll_votes_own_select on public.atelier_poll_votes for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists poll_votes_own_insert on public.atelier_poll_votes;
create policy poll_votes_own_insert on public.atelier_poll_votes for insert to authenticated with check ((select auth.uid()) = user_id and exists (select 1 from public.atelier_polls p where p.id = poll_id and p.active = true));
drop policy if exists poll_results_public_read on public.atelier_poll_results;
create policy poll_results_public_read on public.atelier_poll_results for select to anon, authenticated using (true);

drop policy if exists editorial_picks_public_read on public.editorial_picks;
create policy editorial_picks_public_read on public.editorial_picks for select to anon, authenticated using (active = true or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists editorial_picks_admin_insert on public.editorial_picks;
create policy editorial_picks_admin_insert on public.editorial_picks for insert to authenticated with check ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists editorial_picks_admin_update on public.editorial_picks;
create policy editorial_picks_admin_update on public.editorial_picks for update to authenticated using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin') with check ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists editorial_picks_admin_delete on public.editorial_picks;
create policy editorial_picks_admin_delete on public.editorial_picks for delete to authenticated using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create or replace function public.maintain_atelier_poll_results()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    insert into public.atelier_poll_results(poll_id, option_index, vote_count)
    values (new.poll_id, new.option_index, 1)
    on conflict (poll_id, option_index) do update set vote_count = public.atelier_poll_results.vote_count + 1;
    return new;
  end if;
  return null;
end;
$$;
revoke all on function public.maintain_atelier_poll_results() from public, anon, authenticated;
drop trigger if exists atelier_poll_vote_count_trigger on public.atelier_poll_votes;
create trigger atelier_poll_vote_count_trigger after insert on public.atelier_poll_votes for each row execute function public.maintain_atelier_poll_results();

revoke all privileges on table public.article_collections, public.article_collection_items, public.article_suggestions, public.atelier_polls, public.atelier_poll_votes, public.atelier_poll_results, public.editorial_picks from anon, authenticated, public;
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on public.article_collections to authenticated;
grant select, insert, delete on public.article_collection_items to authenticated;
grant select, insert, update on public.article_suggestions to authenticated;
grant select on public.atelier_polls to anon, authenticated;
grant insert, update on public.atelier_polls to authenticated;
grant select, insert on public.atelier_poll_votes to authenticated;
grant select on public.atelier_poll_results to anon, authenticated;
grant select on public.editorial_picks to anon, authenticated;
grant insert, update, delete on public.editorial_picks to authenticated;
