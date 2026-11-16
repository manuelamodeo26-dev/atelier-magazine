ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS is_admin boolean NOT NULL DEFAULT false;

CREATE OR REPLACE FUNCTION public.enforce_profile_admin_badge()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  actual_admin boolean;
BEGIN
  SELECT COALESCE((u.raw_app_meta_data ->> 'role') = 'admin', false)
    INTO actual_admin
    FROM auth.users AS u
   WHERE u.id = NEW.id;

  NEW.is_admin := COALESCE(actual_admin, false);
  RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.enforce_profile_admin_badge() FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS profiles_enforce_admin_badge ON public.profiles;
CREATE TRIGGER profiles_enforce_admin_badge
BEFORE INSERT OR UPDATE OF is_admin ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.enforce_profile_admin_badge();

CREATE OR REPLACE FUNCTION public.sync_profile_admin_badge_from_auth()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  UPDATE public.profiles
     SET is_admin = COALESCE((NEW.raw_app_meta_data ->> 'role') = 'admin', false)
   WHERE id = NEW.id;
  RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.sync_profile_admin_badge_from_auth() FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS auth_user_sync_profile_admin_badge ON auth.users;
CREATE TRIGGER auth_user_sync_profile_admin_badge
AFTER INSERT OR UPDATE OF raw_app_meta_data ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.sync_profile_admin_badge_from_auth();

UPDATE public.profiles AS p
   SET is_admin = COALESCE((u.raw_app_meta_data ->> 'role') = 'admin', false)
  FROM auth.users AS u
 WHERE u.id = p.id;

GRANT SELECT (is_admin) ON public.profiles TO anon, authenticated;
