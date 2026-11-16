
create or replace function public.validate_atelier_poll_vote()
returns trigger language plpgsql set search_path = ''
as $$
declare option_total integer;
begin
  select jsonb_array_length(options) into option_total
  from public.atelier_polls where id = new.poll_id and active = true;
  if option_total is null then
    raise exception 'Sondaggio non disponibile';
  end if;
  if new.option_index < 0 or new.option_index >= option_total then
    raise exception 'Opzione non valida per questo sondaggio';
  end if;
  return new;
end;
$$;
revoke all on function public.validate_atelier_poll_vote() from public, anon, authenticated;
drop trigger if exists validate_atelier_poll_vote_trigger on public.atelier_poll_votes;
create trigger validate_atelier_poll_vote_trigger before insert on public.atelier_poll_votes
for each row execute function public.validate_atelier_poll_vote();

create or replace function private.redact_article_suggestion_emails()
returns trigger language plpgsql set search_path = ''
as $$
begin
  new.title := regexp_replace(coalesce(new.title,''), '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}', '[email nascosta]', 'gi');
  new.note := regexp_replace(coalesce(new.note,''), '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}', '[email nascosta]', 'gi');
  return new;
end;
$$;
revoke all on function private.redact_article_suggestion_emails() from public, anon, authenticated;
drop trigger if exists redact_article_suggestion_emails_trigger on public.article_suggestions;
create trigger redact_article_suggestion_emails_trigger before insert or update of title,note on public.article_suggestions
for each row execute function private.redact_article_suggestion_emails();
