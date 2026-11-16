drop function if exists public.consume_ghost_quota();
create or replace function public.consume_ghost_quota(p_user_id uuid, p_is_admin boolean)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_now timestamptz := clock_timestamp();
  v_window timestamptz;
  v_count integer;
begin
  if coalesce(auth.jwt() ->> 'role', '') <> 'service_role' then
    raise exception 'Service role required' using errcode = '42501';
  end if;
  if p_user_id is null then
    return jsonb_build_object('allowed', false, 'reason', 'authentication_required');
  end if;
  if not coalesce(p_is_admin, false) then
    v_window := date_trunc('hour', v_now)
      + floor(extract(minute from v_now) / 5) * interval '5 minutes';
    insert into private.ghost_rate_limits(scope_key, window_start, request_count)
    values ('user-burst:' || p_user_id::text, v_window, 1)
    on conflict (scope_key) do update
      set window_start = excluded.window_start,
          request_count = case
            when private.ghost_rate_limits.window_start = excluded.window_start
              then least(private.ghost_rate_limits.request_count + 1, 9)
            else 1
          end
    returning request_count into v_count;
    if v_count > 8 then
      return jsonb_build_object('allowed', false, 'reason', 'user_burst', 'retry_after_seconds', 300);
    end if;
    v_window := date_trunc('day', v_now);
    insert into private.ghost_rate_limits(scope_key, window_start, request_count)
    values ('user-daily:' || p_user_id::text, v_window, 1)
    on conflict (scope_key) do update
      set window_start = excluded.window_start,
          request_count = case
            when private.ghost_rate_limits.window_start = excluded.window_start
              then least(private.ghost_rate_limits.request_count + 1, 61)
            else 1
          end
    returning request_count into v_count;
    if v_count > 60 then
      return jsonb_build_object('allowed', false, 'reason', 'user_daily', 'retry_after_seconds', 86400);
    end if;
  end if;
  v_window := date_trunc('hour', v_now);
  insert into private.ghost_rate_limits(scope_key, window_start, request_count)
  values ('global-hourly', v_window, 1)
  on conflict (scope_key) do update
    set window_start = excluded.window_start,
        request_count = case
          when private.ghost_rate_limits.window_start = excluded.window_start
            then least(private.ghost_rate_limits.request_count + 1, 241)
          else 1
        end
  returning request_count into v_count;
  if v_count > 240 then
    return jsonb_build_object('allowed', false, 'reason', 'global_hourly', 'retry_after_seconds', 3600);
  end if;
  return jsonb_build_object('allowed', true, 'admin', coalesce(p_is_admin, false));
end;
$$;

drop function if exists public.acquire_ghost_slot(uuid);
create or replace function public.acquire_ghost_slot(p_request_id uuid, p_user_id uuid)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare v_active integer;
begin
  if coalesce(auth.jwt() ->> 'role', '') <> 'service_role' then
    raise exception 'Service role required' using errcode = '42501';
  end if;
  if p_request_id is null or p_user_id is null then
    return jsonb_build_object('allowed', false, 'reason', 'invalid_request');
  end if;
  perform pg_catalog.pg_advisory_xact_lock(74201926);
  delete from private.ghost_active_requests where expires_at <= clock_timestamp();
  select count(*) into v_active from private.ghost_active_requests;
  if v_active >= 5 then
    return jsonb_build_object('allowed', false, 'reason', 'concurrency_limit', 'retry_after_seconds', 30);
  end if;
  insert into private.ghost_active_requests(request_id,user_id,expires_at)
  values (p_request_id,p_user_id,clock_timestamp() + interval '3 minutes');
  return jsonb_build_object('allowed', true, 'active', v_active + 1);
exception when unique_violation then
  return jsonb_build_object('allowed', false, 'reason', 'duplicate_request');
end;
$$;

drop function if exists public.release_ghost_slot(uuid);
create or replace function public.release_ghost_slot(p_request_id uuid, p_user_id uuid)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare v_deleted integer;
begin
  if coalesce(auth.jwt() ->> 'role', '') <> 'service_role' then
    raise exception 'Service role required' using errcode = '42501';
  end if;
  if p_request_id is null or p_user_id is null then return false; end if;
  delete from private.ghost_active_requests where request_id = p_request_id and user_id = p_user_id;
  get diagnostics v_deleted = row_count;
  return v_deleted > 0;
end;
$$;

revoke all on function public.consume_ghost_quota(uuid,boolean) from public, anon, authenticated;
revoke all on function public.acquire_ghost_slot(uuid,uuid) from public, anon, authenticated;
revoke all on function public.release_ghost_slot(uuid,uuid) from public, anon, authenticated;
grant execute on function public.consume_ghost_quota(uuid,boolean) to service_role;
grant execute on function public.acquire_ghost_slot(uuid,uuid) to service_role;
grant execute on function public.release_ghost_slot(uuid,uuid) to service_role;
