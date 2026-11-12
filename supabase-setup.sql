-- ATELIER: account, personal feed and saved articles.
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now()
);
create table if not exists public.user_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  categories text[] not null default array['Fashion','Streetwear','Design','Art & Culture','Technology','Architecture','Business','Lifestyle']::text[],
  updated_at timestamptz not null default now()
);
create table if not exists public.saved_articles (
  user_id uuid not null references auth.users(id) on delete cascade,
  article_id text not null,
  title text not null,
  category text,
  excerpt text,
  source text,
  url text,
  image text,
  saved_at timestamptz not null default now(),
  primary key (user_id, article_id)
);

alter table public.profiles enable row level security;
alter table public.user_preferences enable row level security;
alter table public.saved_articles enable row level security;

drop policy if exists profile_select_own on public.profiles;
drop policy if exists profile_update_own on public.profiles;
drop policy if exists preferences_select_own on public.user_preferences;
drop policy if exists preferences_insert_own on public.user_preferences;
drop policy if exists preferences_update_own on public.user_preferences;
drop policy if exists saved_select_own on public.saved_articles;
drop policy if exists saved_insert_own on public.saved_articles;
drop policy if exists saved_delete_own on public.saved_articles;

create policy profile_select_own on public.profiles
  for select to authenticated using ((select auth.uid()) = id);
create policy profile_update_own on public.profiles
  for update to authenticated using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

create policy preferences_select_own on public.user_preferences
  for select to authenticated using ((select auth.uid()) = user_id);
create policy preferences_insert_own on public.user_preferences
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy preferences_update_own on public.user_preferences
  for update to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create policy saved_select_own on public.saved_articles
  for select to authenticated using ((select auth.uid()) = user_id);
create policy saved_insert_own on public.saved_articles
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy saved_delete_own on public.saved_articles
  for delete to authenticated using ((select auth.uid()) = user_id);

grant usage on schema public to authenticated;
grant select, update on public.profiles to authenticated;
grant select, insert, update on public.user_preferences to authenticated;
grant select, insert, delete on public.saved_articles to authenticated;

create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', ''));
  insert into public.user_preferences (user_id) values (new.id);
  return new;
end;
$$;
revoke all on function private.handle_new_user() from public, anon, authenticated;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure private.handle_new_user();


-- Mi piace: un voto per utente e articolo, con conteggi pubblici.
create table if not exists public.article_likes (
  user_id uuid not null references auth.users(id) on delete cascade,
  article_id text not null,
  liked_at timestamptz not null default now(),
  primary key (user_id, article_id)
);
create table if not exists public.article_like_counts (
  article_id text primary key,
  like_count bigint not null default 0 check (like_count >= 0)
);

alter table public.article_likes enable row level security;
alter table public.article_like_counts enable row level security;

drop policy if exists "Users can read their own article likes" on public.article_likes;
drop policy if exists "Users can like articles as themselves" on public.article_likes;
drop policy if exists "Users can remove their own article likes" on public.article_likes;
drop policy if exists "Anyone can read public article like counts" on public.article_like_counts;
create policy "Users can read their own article likes" on public.article_likes
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "Users can like articles as themselves" on public.article_likes
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "Users can remove their own article likes" on public.article_likes
  for delete to authenticated using ((select auth.uid()) = user_id);
create policy "Anyone can read public article like counts" on public.article_like_counts
  for select to anon, authenticated using (true);

grant select, insert, delete on public.article_likes to authenticated;
grant select on public.article_like_counts to anon, authenticated;

create or replace function public.maintain_article_like_counts()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    insert into public.article_like_counts(article_id, like_count)
    values (new.article_id, 1)
    on conflict (article_id) do update
      set like_count = public.article_like_counts.like_count + 1;
    return new;
  elsif tg_op = 'DELETE' then
    update public.article_like_counts
      set like_count = greatest(like_count - 1, 0)
      where article_id = old.article_id;
    delete from public.article_like_counts
      where article_id = old.article_id and like_count = 0;
    return old;
  end if;
  return null;
end;
$$;
revoke all on function public.maintain_article_like_counts() from public, anon, authenticated;
drop trigger if exists article_likes_update_counts on public.article_likes;
create trigger article_likes_update_counts
  after insert or delete on public.article_likes
  for each row execute function public.maintain_article_like_counts();
