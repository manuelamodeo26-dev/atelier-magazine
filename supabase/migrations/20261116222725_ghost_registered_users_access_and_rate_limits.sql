create schema if not exists private;

create table if not exists private.ghost_rate_limits (
  scope_key text primary key,
  window_start timestamptz not null,
  request_count integer not null default 0 check (request_count >= 0)
);

alter table private.ghost_rate_limits enable row level security;
revoke all on table private.ghost_rate_limits from public, anon, authenticated;

create or replace function public.consume_ghost_quota()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user uuid := auth.uid();
  v_admin boolean := coalesce((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin', false);
  v_now timestamptz := clock_timestamp();
  v_window timestamptz;
  v_count integer;
begin
  if v_user is null then
    return jsonb_build_object('allowed', false, 'reason', 'authentication_required');
  end if;

  if not v_admin then
    v_window := date_trunc('hour', v_now)
      + floor(extract(minute from v_now) / 5) * interval '5 minutes';
    insert into private.ghost_rate_limits(scope_key, window_start, request_count)
    values ('user-burst:' || v_user::text, v_window, 1)
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
    values ('user-daily:' || v_user::text, v_window, 1)
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

  return jsonb_build_object('allowed', true, 'admin', v_admin);
end;
$$;

revoke all on function public.consume_ghost_quota() from public, anon;
grant execute on function public.consume_ghost_quota() to authenticated;
