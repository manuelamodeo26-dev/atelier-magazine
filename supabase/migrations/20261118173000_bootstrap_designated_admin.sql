-- Bootstrap the single designated ATELIER administrator.
-- PRIVACY: before running this file in Supabase SQL Editor, replace the
-- placeholder below with the already-confirmed administrator email.
-- Do not commit that replacement or put the address in source control.
-- This migration never creates users and refuses to proceed if another
-- Auth account already has the admin role.

DO $$
DECLARE
  v_target_email constant text := 'REPLACE_WITH_CONFIRMED_ADMIN_EMAIL';
  v_target_id uuid;
  v_target_count integer;
  v_other_admin_count integer;
  v_profile_admin boolean;
BEGIN
  IF v_target_email = 'REPLACE_WITH_CONFIRMED_ADMIN_EMAIL'
     OR btrim(v_target_email) = ''
  THEN
    RAISE EXCEPTION
      'Replace the administrator email placeholder in Supabase SQL Editor before running this migration.';
  END IF;

  SELECT count(*)
    INTO v_target_count
    FROM auth.users
   WHERE lower(email) = lower(v_target_email)
     AND email_confirmed_at IS NOT NULL;

  IF v_target_count <> 1 THEN
    RAISE EXCEPTION
      'Expected exactly one confirmed Auth account for the supplied administrator email; found %.',
      v_target_count;
  END IF;

  SELECT id
    INTO v_target_id
    FROM auth.users
   WHERE lower(email) = lower(v_target_email)
     AND email_confirmed_at IS NOT NULL
   FOR UPDATE;

  SELECT count(*)
    INTO v_other_admin_count
    FROM auth.users
   WHERE raw_app_meta_data ->> 'role' = 'admin'
     AND id <> v_target_id;

  IF v_other_admin_count <> 0 THEN
    RAISE EXCEPTION
      'Refusing admin bootstrap: found % other admin account(s). Review them explicitly before continuing.',
      v_other_admin_count;
  END IF;

  -- Preserve provider metadata and all unrelated app_metadata keys.
  UPDATE auth.users
     SET raw_app_meta_data =
       COALESCE(raw_app_meta_data, '{}'::jsonb)
       || jsonb_build_object('role', 'admin')
   WHERE id = v_target_id
     AND email_confirmed_at IS NOT NULL;

  -- The existing auth.users trigger synchronizes the public badge. Reassert
  -- it here so this migration also repairs a stale badge deterministically.
  UPDATE public.profiles
     SET is_admin = true
   WHERE id = v_target_id;

  SELECT is_admin
    INTO v_profile_admin
    FROM public.profiles
   WHERE id = v_target_id;

  IF v_profile_admin IS DISTINCT FROM true THEN
    RAISE EXCEPTION
      'The designated account has no synchronized public profile admin badge.';
  END IF;

  IF (
    SELECT count(*)
      FROM auth.users
     WHERE raw_app_meta_data ->> 'role' = 'admin'
  ) <> 1 THEN
    RAISE EXCEPTION
      'Admin bootstrap verification failed: the designated account is not the only admin.';
  END IF;
END;
$$;

-- Harden the existing profile guard. Authorization metadata remains exclusively
-- in Auth app_metadata; public profiles.is_admin is only a synchronized badge.
CREATE OR REPLACE FUNCTION public.protect_profile_admin_fields()
RETURNS trigger
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
BEGIN
  IF (SELECT auth.uid()) IS NOT NULL
     AND COALESCE((SELECT auth.jwt())->'app_metadata'->>'role', '') <> 'admin'
  THEN
    NEW.is_admin := OLD.is_admin;
  END IF;

  RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.protect_profile_admin_fields()
  FROM PUBLIC, anon, authenticated;
