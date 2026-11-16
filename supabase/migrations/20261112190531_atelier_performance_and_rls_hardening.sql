
-- ATELIER: indicizzazione delle FK usate nelle relazioni community.
create index if not exists atelier_lab_messages_author_id_idx
  on public.atelier_lab_messages(author_id);
create index if not exists community_comments_author_id_idx
  on public.community_comments(author_id);
create index if not exists community_discussions_author_id_idx
  on public.community_discussions(author_id);
create index if not exists community_reactions_user_id_idx
  on public.community_reactions(user_id);

-- Rimuove la policy SELECT ridondante: la policy pubblica dei nickname
-- copre già anche gli utenti autenticati.
drop policy if exists profile_select_own on public.profiles;

-- Le funzioni auth vengono valutate una sola volta per query, non per riga.
drop policy if exists "Published discussions are readable" on public.community_discussions;
create policy "Published discussions are readable"
on public.community_discussions for select to anon, authenticated
using (
  status = 'published'
  or author_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
);

drop policy if exists "Authors and admins can edit discussions" on public.community_discussions;
create policy "Authors and admins can edit discussions"
on public.community_discussions for update to authenticated
using (
  author_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
)
with check (
  author_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
);

drop policy if exists "Authors and admins can remove discussions" on public.community_discussions;
create policy "Authors and admins can remove discussions"
on public.community_discussions for delete to authenticated
using (
  author_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
);

drop policy if exists "Comments on visible discussions are readable" on public.community_comments;
create policy "Comments on visible discussions are readable"
on public.community_comments for select to anon, authenticated
using (
  (status = 'published' and exists (
    select 1 from public.community_discussions d
    where d.id = community_comments.discussion_id and d.status = 'published'
  ))
  or author_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
);

drop policy if exists "Authors and admins can remove comments" on public.community_comments;
create policy "Authors and admins can remove comments"
on public.community_comments for delete to authenticated
using (
  author_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
);

drop policy if exists "Reporters and admins can view reports" on public.community_reports;
create policy "Reporters and admins can view reports"
on public.community_reports for select to authenticated
using (
  reporter_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
);

drop policy if exists "Admins can update reports" on public.community_reports;
create policy "Admins can update reports"
on public.community_reports for update to authenticated
using ((select auth.jwt())->'app_metadata'->>'role' = 'admin')
with check ((select auth.jwt())->'app_metadata'->>'role' = 'admin');

drop policy if exists "Authors and admins can delete lab messages" on public.atelier_lab_messages;
create policy "Authors and admins can delete lab messages"
on public.atelier_lab_messages for delete to authenticated
using (
  author_id = (select auth.uid())
  or ((select auth.jwt())->'app_metadata'->>'role') = 'admin'
);
