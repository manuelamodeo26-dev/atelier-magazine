-- The full case-insensitive unique index already enforces uniqueness for every
-- non-NULL nickname. The partial index duplicates it and adds write overhead.
DROP INDEX IF EXISTS public.profiles_display_name_lower_unique;
