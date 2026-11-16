-- Allow anonymous visitors to read only the public profile fields rendered by ATELIER Community.
-- Row visibility remains governed by profiles_public_nickname_read (RLS).
GRANT SELECT (id, display_name, avatar_url, is_admin, bio, location, website, instagram)
ON TABLE public.profiles TO anon;
