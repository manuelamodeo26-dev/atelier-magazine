-- ATELIER: schema account, preferenze feed e articoli salvati.
-- Eseguire una sola volta in Supabase > SQL Editor.
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
create policy "profile_select_own" on public.profiles for select to authenticated using (auth.uid() = id);
create policy "profile_update_own" on public.profiles for update to authenticated using (auth.uid() = id) with check (auth.uid() = id);
create policy "preferences_select_own" on public.user_preferences for select to authenticated using (auth.uid() = user_id);
create policy "preferences_insert_own" on public.user_preferences for insert to authenticated with check (auth.uid() = user_id);
create policy "preferences_update_own" on public.user_preferences for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "saved_select_own" on public.saved_articles for select to authenticated using (auth.uid() = user_id);
create policy "saved_insert_own" on public.saved_articles for insert to authenticated with check (auth.uid() = user_id);
create policy "saved_delete_own" on public.saved_articles for delete to authenticated using (auth.uid() = user_id);
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name',''));
  insert into public.user_preferences (user_id) values (new.id);
  return new;
end;
$$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
for each row execute procedure public.handle_new_user();
