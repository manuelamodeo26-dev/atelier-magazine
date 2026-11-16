
create or replace function public.enforce_community_post_rate_limit()
returns trigger
language plpgsql
as $$
begin
  if tg_table_name = 'community_discussions' then
    if exists (select 1 from public.community_discussions where author_id = new.author_id and created_at > now() - interval '60 seconds') then
      raise exception 'Attendi un minuto prima di aprire una nuova discussione.' using errcode = 'P0001';
    end if;
  elsif tg_table_name = 'community_comments' then
    if exists (select 1 from public.community_comments where author_id = new.author_id and created_at > now() - interval '5 seconds') then
      raise exception 'Attendi qualche secondo prima di pubblicare un altro commento.' using errcode = 'P0001';
    end if;
  end if;
  return new;
end;
$$;
drop trigger if exists community_discussion_rate_limit on public.community_discussions;
create trigger community_discussion_rate_limit before insert on public.community_discussions for each row execute function public.enforce_community_post_rate_limit();
drop trigger if exists community_comment_rate_limit on public.community_comments;
create trigger community_comment_rate_limit before insert on public.community_comments for each row execute function public.enforce_community_post_rate_limit();
create unique index if not exists community_reports_one_open_per_target on public.community_reports(reporter_id,target_type,target_id) where status in ('open','reviewing');
