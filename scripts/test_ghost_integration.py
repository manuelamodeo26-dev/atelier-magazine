from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GhostIntegrationTests(unittest.TestCase):
    def test_ghost_panel_is_inside_the_admin_area(self):
        html = (ROOT / "atelier-hub.html").read_text(encoding="utf-8")
        admin_start = html.index('id="hub-admin"')
        admin_end = html.index("</section>", html.index('id="hub-admin"'))
        admin_markup = html[admin_start:admin_end]
        self.assertIn('class="hub-ghost-panel"', admin_markup)
        for element_id in (
            "ghost-form", "ghost-task", "ghost-context", "ghost-content",
            "ghost-submit", "ghost-status", "ghost-result", "ghost-findings",
        ):
            self.assertIn(f'id="{element_id}"', admin_markup)

    def test_frontend_uses_the_authenticated_session_and_admin_gate(self):
        script = (ROOT / "atelier-hub.js").read_text(encoding="utf-8")
        self.assertIn("user?.app_metadata?.role==='admin'", script)
        self.assertIn("db.auth.getSession()", script)
        self.assertIn("db.functions.invoke('atelier-ghost'", script)
        self.assertIn("Authorization:'Bearer '+token", script)
        self.assertIn("button.disabled=true", script)
        self.assertIn("location.reload()", script)

    def test_edge_function_keeps_jwt_admin_and_secret_checks(self):
        source = (ROOT / "supabase/functions/atelier-ghost/index.ts").read_text(encoding="utf-8")
        self.assertIn('user?.app_metadata?.role !== "admin"', source)
        self.assertIn('Deno.env.get("GROQ_API_KEY")', source)
        self.assertIn("x-client-info", source)
        self.assertIn("x-supabase-api-version", source)
        self.assertIn("new TextEncoder().encode(rawBody).byteLength > 20000", source)
        self.assertIn('"site_diagnostic"', source)


if __name__ == "__main__":
    unittest.main()
