-- ATELIER email privacy: redact email addresses from user-generated community content.
-- Applied to the connected Supabase project as migration hide_emails_in_community_content.

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

create or replace function private.hide_email_addresses(p_text text)
returns text
language sql
immutable
set search_path = ''
as $$
  select regexp_replace(
    coalesce(p_text, ''),
    '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}',
    '[email nascosta]',
    'gi'
  );
$$;

create or replace function private.redact_community_emails()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if tg_table_name = 'community_discussions' then
    new.title := regexp_replace(coalesce(new.title, ''), '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}', '[email nascosta]', 'gi');
    new.body := regexp_replace(coalesce(new.body, ''), '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}', '[email nascosta]', 'gi');
  elsif tg_table_name in ('community_comments', 'atelier_lab_messages') then
    new.body := regexp_replace(coalesce(new.body, ''), '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}', '[email nascosta]', 'gi');
  elsif tg_table_name = 'community_reports' then
    if new.details is not null then
      new.details := regexp_replace(new.details, '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}', '[email nascosta]', 'gi');
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists redact_emails_on_discussions on public.community_discussions;
create trigger redact_emails_on_discussions
before insert or update of title, body on public.community_discussions
for each row execute function private.redact_community_emails();

drop trigger if exists redact_emails_on_comments on public.community_comments;
create trigger redact_emails_on_comments
before insert or update of body on public.community_comments
for each row execute function private.redact_community_emails();

drop trigger if exists redact_emails_on_lab_messages on public.atelier_lab_messages;
create trigger redact_emails_on_lab_messages
before insert or update of body on public.atelier_lab_messages
for each row execute function private.redact_community_emails();

drop trigger if exists redact_emails_on_reports on public.community_reports;
create trigger redact_emails_on_reports
before insert or update of details on public.community_reports
for each row execute function private.redact_community_emails();

update public.community_discussions
set title = private.hide_email_addresses(title),
    body = private.hide_email_addresses(body)
where title ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}'
   or body ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}';

update public.community_comments
set body = private.hide_email_addresses(body)
where body ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}';

update public.atelier_lab_messages
set body = private.hide_email_addresses(body)
where body ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}';

update public.community_reports
set details = private.hide_email_addresses(details)
where details ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}';

revoke all on function private.hide_email_addresses(text) from public, anon, authenticated;
revoke all on function private.redact_community_emails() from public, anon, authenticated;


-- Public profile fields are sanitized by the dedicated migration.
-- Redact personal email addresses from public profile fields.
-- Profile rows are publicly readable, so free-text profile fields must not expose email addresses.

create or replace function private.redact_profile_emails()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_email_pattern constant text := '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}';
begin
  if new.bio is not null then
    new.bio := left(private.hide_email_addresses(new.bio), 280);
  end if;
  if new.location is not null then
    new.location := left(private.hide_email_addresses(new.location), 80);
  end if;
  if new.website is not null and new.website ~* v_email_pattern then
    new.website := null;
  end if;
  if new.instagram is not null and new.instagram ~* v_email_pattern then
    new.instagram := null;
  end if;
  if new.avatar_url is not null and new.avatar_url ~* v_email_pattern then
    new.avatar_url := null;
  end if;
  return new;
end;
$$;

revoke all on function private.redact_profile_emails() from public, anon, authenticated;

drop trigger if exists redact_emails_on_profiles on public.profiles;
create trigger redact_emails_on_profiles
before insert or update of bio, location, website, instagram, avatar_url
on public.profiles
for each row execute function private.redact_profile_emails();

update public.profiles
set
  bio = case when bio is null then null else left(private.hide_email_addresses(bio), 280) end,
  location = case when location is null then null else left(private.hide_email_addresses(location), 80) end,
  website = case when website ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}' then null else website end,
  instagram = case when instagram ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}' then null else instagram end,
  avatar_url = case when avatar_url ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}' then null else avatar_url end
where
  coalesce(bio, '') ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}'
  or coalesce(location, '') ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}'
  or coalesce(website, '') ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}'
  or coalesce(instagram, '') ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}'
  or coalesce(avatar_url, '') ~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}';
