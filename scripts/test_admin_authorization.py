import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
ADMIN_EMAIL_PLACEHOLDER = "REPLACE_WITH_CONFIRMED_ADMIN_EMAIL"


class AdminAuthorizationTests(unittest.TestCase):
    def test_bootstrap_is_guarded_and_keeps_admin_email_out_of_git(self):
        migration = (
            MIGRATIONS / "20261118173000_bootstrap_designated_admin.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn(ADMIN_EMAIL_PLACEHOLDER.lower(), migration)
        self.assertNotIn("@", migration)
        self.assertIn("email_confirmed_at is not null", migration)
        self.assertIn("raw_app_meta_data", migration)
        self.assertIn("jsonb_build_object('role', 'admin')", migration)
        self.assertIn("v_other_admin_count <> 0", migration)
        self.assertIn("refusing admin bootstrap", migration)
        self.assertIn("security invoker", migration)
        self.assertNotIn("raw_user_meta_data", migration)
        self.assertNotIn("user_metadata", migration)

    def test_browser_authorization_uses_auth_app_metadata(self):
        community = (ROOT / "community.js").read_text(encoding="utf-8")
        account = (ROOT / "account.js").read_text(encoding="utf-8")

        self.assertIn("user?.app_metadata?.role==='admin'", community)
        self.assertIn("user?.app_metadata?.role==='admin'", account)
        self.assertNotIn("user?.user_metadata?.role", community + account)

    def test_database_moderation_policies_use_signed_app_metadata(self):
        migration = (
            MIGRATIONS / "20261116181442_admin_comment_moderation.sql"
        ).read_text(encoding="utf-8").lower()
        community = (
            MIGRATIONS / "20261112160628_create_atelier_community.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("auth.jwt()", migration)
        self.assertIn("'app_metadata'->>'role'", migration)
        self.assertIn("'app_metadata'->>'role'", community)
        self.assertNotIn("user_metadata", migration + community)

    def test_public_badge_is_derived_from_auth_app_metadata(self):
        badge = (
            MIGRATIONS / "20261116143742_public_admin_badges.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("raw_app_meta_data ->> 'role'", badge)
        self.assertIn("auth_user_sync_profile_admin_badge", badge)
        self.assertIn("new.is_admin :=", badge)

    def test_sql_verification_script_is_privacy_safe_and_checks_forgery(self):
        verification = (
            ROOT / "supabase" / "tests" / "admin_authorization.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn(ADMIN_EMAIL_PLACEHOLDER.lower(), verification)
        self.assertNotIn("@", verification)
        self.assertIn("has_table_privilege", verification)
        self.assertIn("pg_policies", verification)
        self.assertIn("app_metadata", verification)
        self.assertIn("set local role authenticated", verification)
        self.assertIn("update public.profiles", verification)
        self.assertIn("rollback", verification)


if __name__ == "__main__":
    unittest.main()
