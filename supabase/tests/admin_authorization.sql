-- Post-migration verification for THE ATELIER VERSE.
-- In Supabase SQL Editor, replace the placeholder with the confirmed admin
-- email before running. Do not commit the replaced value.
-- The runtime badge-forgery check is rolled back and leaves no data changes.

DO $$
DECLARE
  v_target_email constant text := 'REPLACE_WITH_CONFIRMED_ADMIN_EMAIL';
  v_target_id uuid;
  v_target_count integer;
  v_admin_count integer;
  v_badge boolean;
  v_policy_count integer := 0;
  v_policy record;
  v_expression text;
BEGIN
  IF v_target_email = 'REPLACE_WITH_CONFIRMED_ADMIN_EMAIL'
     OR btrim(v_target_email) = ''
  THEN
    RAISE EXCEPTION 'Replace the administrator email placeholder before running this verification.';
  END IF;

  SELECT count(*)
    INTO v_target_count
    FROM auth.users
   WHERE lower(email) = lower(v_target_email)
     AND email_confirmed_at IS NOT NULL;

  IF v_target_count <> 1 THEN
    RAISE EXCEPTION 'Expected one confirmed designated account; found %.', v_target_count;
  END IF;

  SELECT id
    INTO v_target_id
    FROM auth.users
   WHERE lower(email) = lower(v_target_email)
     AND email_confirmed_at IS NOT NULL;

  SELECT count(*)
    INTO v_admin_count
    FROM auth.users
   WHERE raw_app_meta_data ->> 'role' = 'admin';

  IF v_admin_count <> 1
     OR NOT EXISTS (
       SELECT 1 FROM auth.users
        WHERE id = v_target_id
          AND raw_app_meta_data ->> 'role' = 'admin'
     )
  THEN
    RAISE EXCEPTION 'The designated account is not the unique Auth administrator.';
  END IF;

  SELECT is_admin
    INTO v_badge
    FROM public.profiles
   WHERE id = v_target_id;

  IF v_badge IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'The public profile badge is not synchronized.';
  END IF;

  IF has_table_privilege('anon', 'auth.users', 'UPDATE')
     OR has_table_privilege('authenticated', 'auth.users', 'UPDATE')
     OR has_column_privilege('anon', 'auth.users', 'raw_app_meta_data', 'UPDATE')
     OR has_column_privilege('authenticated', 'auth.users', 'raw_app_meta_data', 'UPDATE')
  THEN
    RAISE EXCEPTION 'A public API role can update Auth authorization metadata.';
  END IF;

  IF NOT EXISTS (
    SELECT 1
      FROM pg_trigger t
      JOIN pg_class c ON c.oid = t.tgrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'public'
       AND c.relname = 'profiles'
       AND t.tgname = 'protect_profile_admin_fields'
       AND NOT t.tgisinternal
       AND t.tgenabled <> 'D'
  ) THEN
    RAISE EXCEPTION 'The profile admin-field protection trigger is missing or disabled.';
  END IF;

  IF EXISTS (
    SELECT 1
      FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = 'public'
       AND p.proname = 'protect_profile_admin_fields'
       AND p.prosecdef
  ) THEN
    RAISE EXCEPTION 'The profile guard must run as SECURITY INVOKER.';
  END IF;

  -- Existing moderation policies must authorize via signed app_metadata JWT claims.
  FOR v_policy IN
    SELECT tablename, policyname, qual, with_check
      FROM pg_policies
     WHERE schemaname = 'public'
       AND policyname IN (
         'Admins can moderate comments',
         'Authors and admins can edit discussions',
         'Authors and admins can remove discussions',
         'Authors and admins can remove comments',
         'Admins can update reports'
       )
  LOOP
    v_expression := COALESCE(v_policy.qual, '') || ' ' || COALESCE(v_policy.with_check, '');
    IF position('app_metadata' IN v_expression) = 0
       OR position('user_metadata' IN v_expression) > 0
    THEN
      RAISE EXCEPTION 'Unsafe or missing server-side role check in policy % on %.',
        v_policy.policyname, v_policy.tablename;
    END IF;
    v_policy_count := v_policy_count + 1;
  END LOOP;

  IF v_policy_count <> 5 THEN
    RAISE EXCEPTION 'Expected all 5 moderation policies; found %.', v_policy_count;
  END IF;

  RAISE NOTICE
    'PASS: unique confirmed administrator, synchronized badge, no client Auth metadata writes, protected profile badge, and 5 app_metadata-based moderation policies.';
END;
$$;

-- Runtime regression check: a normal authenticated user cannot forge the badge.
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM auth.users
     WHERE raw_app_meta_data ->> 'role' IS DISTINCT FROM 'admin'
  ) THEN
    RAISE EXCEPTION 'A non-admin test account is required for the badge-forgery check.';
  END IF;
END;
$$;

SELECT set_config(
  'atelier.admin_test_user_id',
  (
    SELECT id::text
      FROM auth.users
     WHERE raw_app_meta_data ->> 'role' IS DISTINCT FROM 'admin'
     ORDER BY created_at
     LIMIT 1
  ),
  true
);

SET LOCAL ROLE authenticated;

SELECT set_config('request.jwt.claim.sub', current_setting('atelier.admin_test_user_id'), true);
SELECT set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub', current_setting('atelier.admin_test_user_id'),
    'role', 'authenticated',
    'app_metadata', '{}'::jsonb
  )::text,
  true
);

UPDATE public.profiles
   SET is_admin = true
 WHERE id = auth.uid();

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
      FROM public.profiles
     WHERE id = auth.uid()
       AND is_admin IS TRUE
  ) THEN
    RAISE EXCEPTION 'A normal authenticated user was able to forge the admin badge.';
  END IF;
END;
$$;

RESET ROLE;
ROLLBACK;
