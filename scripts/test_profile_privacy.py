import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProfileEmailPrivacyTests(unittest.TestCase):
    def test_public_profile_text_is_redacted_before_render(self):
        source = (ROOT / "community.js").read_text(encoding="utf-8")
        self.assertIn("esc(hideEmails(p.location))", source)
        self.assertIn("esc(hideEmails(p.bio))", source)

    def test_database_trigger_covers_public_profile_fields(self):
        migration = (
            ROOT / "supabase" / "migrations" /
            "20261117125404_redact_emails_in_public_profiles.sql"
        ).read_text(encoding="utf-8").lower()
        self.assertIn("create trigger redact_emails_on_profiles", migration)
        for field in ("new.bio", "new.location", "new.website", "new.instagram", "new.avatar_url"):
            self.assertIn(field, migration)


if __name__ == "__main__":
    unittest.main()
