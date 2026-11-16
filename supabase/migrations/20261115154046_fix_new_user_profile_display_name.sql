create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $function$
declare
  candidate text;
begin
  candidate := regexp_replace(coalesce(new.raw_user_meta_data ->> 'display_name', ''), '[^A-Za-z0-9_]', '', 'g');
  if length(candidate) < 3 or length(candidate) > 20 then
    candidate := 'member_' || left(replace(new.id::text, '-', ''), 8);
  end if;

  insert into public.profiles (id, display_name)
  values (new.id, candidate);

  insert into public.user_preferences (user_id)
  values (new.id);

  return new;
end;
$function$;