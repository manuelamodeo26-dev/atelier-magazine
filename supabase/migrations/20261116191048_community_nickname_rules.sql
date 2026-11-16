alter table public.profiles
  add constraint profiles_display_name_format_check
  check (display_name is null or display_name ~ '^[A-Za-z0-9_]{3,20}$');

alter table public.profiles
  add constraint profiles_display_name_reserved_check
  check (display_name is null or lower(display_name) not in ('admin','administrator','moderator','moderatore','support','assistenza'));

create unique index profiles_display_name_lower_unique
  on public.profiles (lower(display_name))
  where display_name is not null;