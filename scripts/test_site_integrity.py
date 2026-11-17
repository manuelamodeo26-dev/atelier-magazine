#!/usr/bin/env python3
"""Static integrity checks for ATELIER's GitHub Pages site."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = set()
        self.title_seen = False
        self.viewport_seen = False
        self.lang_seen = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            value = attrs["id"]
            if value in self.ids:
                raise AssertionError("ID HTML duplicato: " + value)
            self.ids.add(value)
        if tag == "html":
            self.lang_seen = bool(attrs.get("lang"))
        if tag == "title":
            self.title_seen = True
        if tag == "meta" and attrs.get("name", "").lower() == "viewport":
            self.viewport_seen = True
        for key in ("src", "href"):
            value = attrs.get(key)
            if value:
                self.references.append(value)


def local_target(page, reference):
    parsed = urlsplit(reference.strip())
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    if path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = page.parent / path
    target = target.resolve()
    if target.is_dir():
        target = target / "index.html"
    return target


def main():
    pages = sorted(ROOT.glob("*.html"))
    assert pages, "Nessuna pagina HTML trovata"
    checked = 0
    for page in pages:
        parser = SiteParser()
        parser.feed(page.read_text(encoding="utf-8"))
        assert parser.lang_seen, f"{page.name}: manca lang su html"
        assert parser.title_seen, f"{page.name}: manca il titolo"
        assert parser.viewport_seen, f"{page.name}: manca meta viewport"
        for reference in parser.references:
            target = local_target(page, reference)
            if target is None:
                continue
            assert target.is_file(), (
                f"{page.name}: riferimento locale non trovato: {reference}"
            )
            checked += 1
    css_files = sorted(ROOT.glob("*.css"))
    css = "\n".join(path.read_text(encoding="utf-8") for path in css_files)
    defined_variables = set(re.findall(r"(--[\w-]+)\s*:", css))
    referenced_variables = set(re.findall(r"var\(\s*(--[\w-]+)", css))
    missing_variables = referenced_variables - defined_variables
    assert not missing_variables, (
        "Variabili CSS non definite: " + ", ".join(sorted(missing_variables))
    )
    assert not re.search(r"var\(\s*--[\w-]+\s*\)[A-Za-z0-9#_-]", css), (
        "Possibile suffisso CSS non valido dopo una variabile var()"
    )

    home = (ROOT / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
    assert "'./account.html'" in service_worker, (
        "Service worker: la pagina account non è inclusa nella cache iniziale"
    )
    manifest = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest.get("name") and manifest.get("start_url"), (
        "Manifest PWA: nome o start_url mancante"
    )
    icons = manifest.get("icons", [])
    assert icons and all((ROOT / icon["src"]).is_file() for icon in icons), (
        "Manifest PWA: icone mancanti o file non trovato"
    )
    assert 'id="maintenance-screen"' in home, "Homepage: schermata manutenzione assente"
    assert "data.archive_status!=='active'" in app, "Homepage: manca il blocco fail-closed"
    assert "setMaintenanceMode(true)" in app, "Homepage: la modalità manutenzione non viene applicata"
    print(f"Integrità sito OK: {len(pages)} pagine HTML, {checked} riferimenti locali verificati; manutenzione fail-closed verificata.")


EXPECTED_MIGRATIONS = {
    "20261112160628_create_atelier_community.sql",
    "20261112160637_community_rate_limits_and_report_guard.sql",
    "20261112160813_secure_community_rate_limit_function.sql",
    "20261112165421_create_atelier_lab_shared_writing_space.sql",
    "20261112180739_hide_emails_in_community_content.sql",
    "20261112180753_make_email_redaction_trigger_self_contained.sql",
    "20261112181009_community_nicknames_and_public_profiles.sql",
    "20261112182027_atelier_hub_features.sql",
    "20261112182127_atelier_hub_validation.sql",
    "20261112182224_atelier_hub_performance_indexes.sql",
    "20261112182238_atelier_hub_rls_initplan_tuning.sql",
    "20261112184158_fix_email_redaction_regex.sql",
    "20261112190531_atelier_performance_and_rls_hardening.sql",
    "20261112192729_add_user_profile_avatars.sql",
    "20261115154046_fix_new_user_profile_display_name.sql",
    "20261115213608_fix_duplicate_profile_display_name.sql",
    "20261116143742_public_admin_badges.sql",
    "20261116181442_admin_comment_moderation.sql",
    "20261116190307_community_comment_archived_status.sql",
    "20261116190433_community_replies_and_richer_profiles.sql",
    "20261116190527_secure_community_reply_targets.sql",
    "20261116191048_community_nickname_rules.sql",
    "20261116211525_secure_profile_trigger_and_comment_reply_policy.sql",
    "20261116211618_community_nested_reply_parent_validation.sql",
    "20261116212723_remove_redundant_profile_nickname_index.sql",
    "20261116220535_grant_public_profile_fields_to_anon.sql",
    "20261116222725_ghost_registered_users_access_and_rate_limits.sql",
    "20261116223138_ghost_global_concurrency_slots.sql",
    "20261116223546_ghost_quota_rpc_service_role_only.sql",
    "20261117125404_redact_emails_in_public_profiles.sql",
}


class AdminAuthorizationTests(unittest.TestCase):
    def test_browser_admin_checks_use_trusted_app_metadata(self):
        account = (ROOT / "account.js").read_text(encoding="utf-8")
        community = (ROOT / "community.js").read_text(encoding="utf-8")
        hub = (ROOT / "atelier-hub.js").read_text(encoding="utf-8")
        self.assertIn("user?.app_metadata?.role==='admin'", account)
        self.assertIn("user?.app_metadata?.role==='admin'", community)
        self.assertIn("user?.app_metadata?.role==='admin'", hub)
        self.assertNotIn("user?.user_metadata?.role", account + community + hub)

    def test_maintenance_bypass_requires_admin_access_event(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        account = (ROOT / "account.js").read_text(encoding="utf-8")
        self.assertIn("event.detail?.isAdmin===true", app)
        self.assertIn("window.ATELIER_SET_ADMIN_ACCESS?.(isAdmin)", account)
        self.assertIn("adminMaintenanceAccess=isAdmin===true", app)

    def test_ghost_rechecks_admin_role_on_server(self):
        function = (ROOT / "supabase" / "functions" / "atelier-ghost" / "index.ts")
        self.assertTrue(function.is_file(), "ATELIER Ghost: file funzione non trovata")
        source = function.read_text(encoding="utf-8")
        self.assertIn('const isAdmin = user?.app_metadata?.role === "admin";', source)
        self.assertIn("const allowedTasks = isAdmin", source)
        self.assertIn('["review_content"]', source)
        self.assertIn('"review_report", "site_diagnostic"', source)
        self.assertIn("consume_ghost_quota", source)
        self.assertIn("acquire_ghost_slot", source)
        self.assertIn("release_ghost_slot", source)
        self.assertNotIn("user?.user_metadata?.role", source)



class MigrationRepositoryTests(unittest.TestCase):
    def test_all_applied_migrations_are_versioned_in_repository(self):
        directory = ROOT / "supabase" / "migrations"
        actual = {path.name for path in directory.glob("*.sql")}
        self.assertEqual(actual, EXPECTED_MIGRATIONS)

    def test_migration_files_are_non_empty_and_versioned(self):
        directory = ROOT / "supabase" / "migrations"
        for path in directory.glob("*.sql"):
            self.assertRegex(path.name, r"^\d{14}_[a-z0-9_]+\.sql$")
            self.assertTrue(path.read_text(encoding="utf-8").strip(), path.name)


if __name__ == "__main__":
    main()
