alter table public.profiles add column if not exists avatar_url text;
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', true, 5242880, array['image/jpeg','image/png','image/webp','image/avif'])
on conflict (id) do update set public = true, file_size_limit = 5242880, allowed_mime_types = array['image/jpeg','image/png','image/webp','image/avif'];
drop policy if exists "ATELIER avatar images are publicly readable" on storage.objects;
drop policy if exists "ATELIER users upload own avatar" on storage.objects;
drop policy if exists "ATELIER users update own avatar" on storage.objects;
drop policy if exists "ATELIER users delete own avatar" on storage.objects;
create policy "ATELIER avatar images are publicly readable" on storage.objects for select using (bucket_id = 'avatars');
create policy "ATELIER users upload own avatar" on storage.objects for insert to authenticated with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "ATELIER users update own avatar" on storage.objects for update to authenticated using (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text) with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "ATELIER users delete own avatar" on storage.objects for delete to authenticated using (bucket_id = 'avatars' and (storage.foldername(name))[1] = (select auth.uid())::text);
grant select, insert, update on public.profiles to authenticated;
