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
