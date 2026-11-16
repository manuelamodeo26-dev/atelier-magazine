from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GhostIntegrationTests(unittest.TestCase):
    def test_member_workspace_is_separate_and_requires_login(self):
        html = (ROOT / "ghost.html").read_text(encoding="utf-8")
        for element_id in (
            "ghost-auth-required", "ghost-workspace", "ghost-form", "ghost-task",
            "ghost-context", "ghost-content", "ghost-submit", "ghost-status",
            "ghost-result", "ghost-findings",
        ):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn("./settings.html", html)

    def test_frontend_requires_verified_authenticated_user(self):
        script = (ROOT / "ghost.js").read_text(encoding="utf-8")
        self.assertIn("db.auth.getUser()", script)
        self.assertIn("db.functions.invoke('atelier-ghost'", script)
        self.assertIn("Authorization:'Bearer '+token", script)
        self.assertIn("button.disabled=true", script)
        self.assertIn("data-admin-only", (ROOT / "ghost.html").read_text(encoding="utf-8"))

    def test_edge_function_enforces_member_and_admin_scopes(self):
        source = (ROOT / "supabase/functions/atelier-ghost/index.ts").read_text(encoding="utf-8")
        self.assertIn('user?.app_metadata?.role === "admin"', source)
        self.assertIn('["review_content"]', source)
        self.assertIn('"review_report", "site_diagnostic"', source)
        self.assertIn("consume_ghost_quota", source)
        self.assertIn("user_burst", source)
        self.assertIn("user_daily", source)
        self.assertIn("global_hourly", source)
        self.assertIn("if (!groqKey && !geminiKey)", source)
        self.assertIn("GROQ_API_KEY oppure GEMINI_API_KEY", source)
        self.assertIn("new TextEncoder().encode(rawBody).byteLength > 20000", source)

    def test_dedicated_settings_page_has_persisted_controls(self):
        html = (ROOT / "settings.html").read_text(encoding="utf-8")
        script = (ROOT / "settings.js").read_text(encoding="utf-8")
        for element_id in ("profile-form", "preferences-form", "email-form", "password-form",
                           "remember-session", "signout-others", "signout-current"):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn("user_preferences", script)
        self.assertIn("profiles').update", script)
        self.assertIn("auth.updateUser({password})", script)
        self.assertIn("auth.signOut({scope:'others'})", script)


if __name__ == "__main__":
    unittest.main()
