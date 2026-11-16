
create index if not exists article_collection_items_collection_user_idx on public.article_collection_items(collection_id,user_id);
create index if not exists article_collection_items_user_idx on public.article_collection_items(user_id);
create index if not exists article_suggestions_user_created_idx on public.article_suggestions(user_id,created_at desc);
create index if not exists article_suggestions_reviewed_by_idx on public.article_suggestions(reviewed_by);
create index if not exists atelier_poll_votes_user_idx on public.atelier_poll_votes(user_id);
create index if not exists atelier_polls_created_by_idx on public.atelier_polls(created_by);
create index if not exists editorial_picks_updated_by_idx on public.editorial_picks(updated_by);

drop policy if exists suggestions_own_select on public.article_suggestions;
create policy suggestions_own_select on public.article_suggestions for select to authenticated
using ((select auth.uid()) = user_id or (select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists suggestions_admin_update on public.article_suggestions;
create policy suggestions_admin_update on public.article_suggestions for update to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin')
with check ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists polls_public_read on public.atelier_polls;
create policy polls_public_read on public.atelier_polls for select to anon, authenticated
using (active = true or (select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists polls_admin_insert on public.atelier_polls;
create policy polls_admin_insert on public.atelier_polls for insert to authenticated
with check ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists polls_admin_update on public.atelier_polls;
create policy polls_admin_update on public.atelier_polls for update to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin')
with check ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists editorial_picks_public_read on public.editorial_picks;
create policy editorial_picks_public_read on public.editorial_picks for select to anon, authenticated
using (active = true or (select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists editorial_picks_admin_insert on public.editorial_picks;
create policy editorial_picks_admin_insert on public.editorial_picks for insert to authenticated
with check ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists editorial_picks_admin_update on public.editorial_picks;
create policy editorial_picks_admin_update on public.editorial_picks for update to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin')
with check ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
drop policy if exists editorial_picks_admin_delete on public.editorial_picks;
create policy editorial_picks_admin_delete on public.editorial_picks for delete to authenticated
using ((select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
