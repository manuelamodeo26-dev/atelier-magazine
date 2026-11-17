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
