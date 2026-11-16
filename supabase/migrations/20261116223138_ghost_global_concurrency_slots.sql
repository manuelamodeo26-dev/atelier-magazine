alter table private.ghost_rate_limits disable row level security;

create table if not exists private.ghost_active_requests (
  request_id uuid primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  started_at timestamptz not null default now(),
  expires_at timestamptz not null
);
revoke all on table private.ghost_active_requests from public, anon, authenticated;

create or replace function public.acquire_ghost_slot(p_request_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user uuid := auth.uid();
  v_active integer;
begin
  if v_user is null then
    return jsonb_build_object('allowed', false, 'reason', 'authentication_required');
  end if;
  perform pg_catalog.pg_advisory_xact_lock(74201926);
  delete from private.ghost_active_requests where expires_at <= clock_timestamp();
  select count(*) into v_active from private.ghost_active_requests;
  if v_active >= 5 then
    return jsonb_build_object('allowed', false, 'reason', 'concurrency_limit', 'retry_after_seconds', 30);
  end if;
  insert into private.ghost_active_requests(request_id,user_id,expires_at)
  values (p_request_id,v_user,clock_timestamp() + interval '3 minutes');
  return jsonb_build_object('allowed', true, 'active', v_active + 1);
exception when unique_violation then
  return jsonb_build_object('allowed', false, 'reason', 'duplicate_request');
end;
$$;

create or replace function public.release_ghost_slot(p_request_id uuid)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user uuid := auth.uid();
  v_admin boolean := coalesce((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin', false);
  v_deleted integer;
begin
  if v_user is null then return false; end if;
  delete from private.ghost_active_requests
   where request_id = p_request_id
     and (user_id = v_user or v_admin);
  get diagnostics v_deleted = row_count;
  return v_deleted > 0;
end;
$$;

revoke all on function public.acquire_ghost_slot(uuid) from public, anon;
revoke all on function public.release_ghost_slot(uuid) from public, anon;
grant execute on function public.acquire_ghost_slot(uuid) to authenticated;
grant execute on function public.release_ghost_slot(uuid) to authenticated;
