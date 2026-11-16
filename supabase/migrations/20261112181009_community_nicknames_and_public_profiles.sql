create unique index if not exists profiles_display_name_ci_unique on public.profiles (lower(display_name));
alter table public.profiles drop constraint if exists profiles_display_name_format;
alter table public.profiles add constraint profiles_display_name_format
check (display_name ~ '^[A-Za-z0-9_]{3,20}$');
drop policy if exists profiles_public_nickname_read on public.profiles;
create policy profiles_public_nickname_read on public.profiles
for select to anon, authenticated using (true);
drop policy if exists profiles_insert_own on public.profiles;
create policy profiles_insert_own on public.profiles
for insert to authenticated with check ((select auth.uid()) = id);
