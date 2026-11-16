
create table if not exists public.atelier_lab_messages (
  id uuid primary key default gen_random_uuid(),
  author_id uuid not null references auth.users(id) on delete cascade,
  body text not null check (char_length(btrim(body)) between 1 and 2000),
  created_at timestamptz not null default now()
);
create index if not exists atelier_lab_messages_created_idx on public.atelier_lab_messages (created_at desc);
alter table public.atelier_lab_messages enable row level security;
grant select, insert, delete on public.atelier_lab_messages to authenticated;
drop policy if exists "Lab members can read messages" on public.atelier_lab_messages;
create policy "Lab members can read messages" on public.atelier_lab_messages
for select to authenticated using (true);
drop policy if exists "Members can write their own lab messages" on public.atelier_lab_messages;
create policy "Members can write their own lab messages" on public.atelier_lab_messages
for insert to authenticated with check ((select auth.uid()) = author_id);
drop policy if exists "Authors and admins can delete lab messages" on public.atelier_lab_messages;
create policy "Authors and admins can delete lab messages" on public.atelier_lab_messages
for delete to authenticated using (
  (select auth.uid()) = author_id
  or (select auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
);
