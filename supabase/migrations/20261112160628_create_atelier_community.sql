
create table if not exists public.community_discussions (
  id uuid primary key default gen_random_uuid(),
  author_id uuid not null references auth.users(id) on delete cascade,
  title text not null check (char_length(title) between 8 and 140),
  body text not null check (char_length(body) between 20 and 5000),
  category text not null check (category in ('Fashion','Streetwear','Design','Art & Culture','Fashion Industry','Your Style','Off Topic')),
  status text not null default 'published' check (status in ('published','hidden','removed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists public.community_comments (
  id uuid primary key default gen_random_uuid(),
  discussion_id uuid not null references public.community_discussions(id) on delete cascade,
  author_id uuid not null references auth.users(id) on delete cascade,
  body text not null check (char_length(body) between 2 and 2000),
  status text not null default 'published' check (status in ('published','hidden','removed')),
  created_at timestamptz not null default now()
);
create table if not exists public.community_reactions (
  discussion_id uuid not null references public.community_discussions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (discussion_id,user_id)
);
create table if not exists public.community_reports (
  id uuid primary key default gen_random_uuid(),
  reporter_id uuid not null references auth.users(id) on delete cascade,
  target_type text not null check (target_type in ('discussion','comment')),
  target_id uuid not null,
  reason text not null check (reason in ('spam','harassment','hate','inappropriate','privacy','copyright','other')),
  details text check (details is null or char_length(details) <= 1000),
  status text not null default 'open' check (status in ('open','reviewing','resolved','dismissed')),
  created_at timestamptz not null default now()
);
create index if not exists community_discussions_feed_idx on public.community_discussions(status,created_at desc);
create index if not exists community_comments_discussion_idx on public.community_comments(discussion_id,created_at asc);
create index if not exists community_reports_status_idx on public.community_reports(status,created_at desc);
alter table public.community_discussions enable row level security;
alter table public.community_comments enable row level security;
alter table public.community_reactions enable row level security;
alter table public.community_reports enable row level security;
grant select on public.community_discussions, public.community_comments, public.community_reactions to anon, authenticated;
grant insert, update, delete on public.community_discussions to authenticated;
grant insert, update, delete on public.community_comments to authenticated;
grant select, insert, delete on public.community_reactions to authenticated;
grant select, insert, update on public.community_reports to authenticated;
drop policy if exists "Published discussions are readable" on public.community_discussions;
create policy "Published discussions are readable" on public.community_discussions for select to anon, authenticated using (status = 'published' or author_id = (select auth.uid()) or (auth.jwt()->'app_metadata'->>'role') = 'admin');
drop policy if exists "Signed in users can start discussions" on public.community_discussions;
create policy "Signed in users can start discussions" on public.community_discussions for insert to authenticated with check (author_id = (select auth.uid()) and status = 'published');
drop policy if exists "Authors and admins can edit discussions" on public.community_discussions;
create policy "Authors and admins can edit discussions" on public.community_discussions for update to authenticated using (author_id = (select auth.uid()) or (auth.jwt()->'app_metadata'->>'role') = 'admin') with check (author_id = (select auth.uid()) or (auth.jwt()->'app_metadata'->>'role') = 'admin');
drop policy if exists "Authors and admins can remove discussions" on public.community_discussions;
create policy "Authors and admins can remove discussions" on public.community_discussions for delete to authenticated using (author_id = (select auth.uid()) or (auth.jwt()->'app_metadata'->>'role') = 'admin');
drop policy if exists "Comments on visible discussions are readable" on public.community_comments;
create policy "Comments on visible discussions are readable" on public.community_comments for select to anon, authenticated using (status = 'published' and exists (select 1 from public.community_discussions d where d.id = discussion_id and d.status = 'published') or author_id = (select auth.uid()) or (auth.jwt()->'app_metadata'->>'role') = 'admin');
drop policy if exists "Signed in users can comment on visible discussions" on public.community_comments;
create policy "Signed in users can comment on visible discussions" on public.community_comments for insert to authenticated with check (author_id = (select auth.uid()) and status = 'published' and exists (select 1 from public.community_discussions d where d.id = discussion_id and d.status = 'published'));
drop policy if exists "Authors and admins can remove comments" on public.community_comments;
create policy "Authors and admins can remove comments" on public.community_comments for delete to authenticated using (author_id = (select auth.uid()) or (auth.jwt()->'app_metadata'->>'role') = 'admin');
drop policy if exists "Reactions are publicly readable" on public.community_reactions;
create policy "Reactions are publicly readable" on public.community_reactions for select to anon, authenticated using (true);
drop policy if exists "Users manage their own reactions" on public.community_reactions;
create policy "Users manage their own reactions" on public.community_reactions for insert to authenticated with check (user_id = (select auth.uid()));
drop policy if exists "Users remove their own reactions" on public.community_reactions;
create policy "Users remove their own reactions" on public.community_reactions for delete to authenticated using (user_id = (select auth.uid()));
drop policy if exists "Users can file reports" on public.community_reports;
create policy "Users can file reports" on public.community_reports for insert to authenticated with check (reporter_id = (select auth.uid()));
drop policy if exists "Reporters and admins can view reports" on public.community_reports;
create policy "Reporters and admins can view reports" on public.community_reports for select to authenticated using (reporter_id = (select auth.uid()) or (auth.jwt()->'app_metadata'->>'role') = 'admin');
drop policy if exists "Admins can update reports" on public.community_reports;
create policy "Admins can update reports" on public.community_reports for update to authenticated using ((auth.jwt()->'app_metadata'->>'role') = 'admin') with check ((auth.jwt()->'app_metadata'->>'role') = 'admin');
