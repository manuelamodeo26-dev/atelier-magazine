
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
