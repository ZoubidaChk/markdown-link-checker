import importlib.util
import json
import pathlib
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "markdown_link_checker.py"

spec = importlib.util.spec_from_file_location("markdown_link_checker", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


class MarkdownLinkCheckerTests(unittest.TestCase):
    def test_extracts_links_images_and_titles(self):
        text = "[Docs](https://example.com) ![Logo](logo.png \"Logo\")"

        self.assertEqual(
            checker.extract(text),
            [
                {"label": "Docs", "url": "https://example.com"},
                {"label": "Logo", "url": "logo.png"},
            ],
        )

    def test_check_local_handles_existing_missing_and_anchor_links(self):
        root = pathlib.Path(__file__).parent
        existing = root / "_existing.md"
        existing.write_text("content", encoding="utf-8")
        try:
            self.assertEqual(checker.check_local("_existing.md#intro", root), {"url": "_existing.md#intro", "ok": True})
            self.assertEqual(checker.check_local("_missing.md", root), {"url": "_missing.md", "ok": False})
            self.assertEqual(checker.check_local("#intro", root), {"url": "#intro", "ok": True})
        finally:
            existing.unlink(missing_ok=True)

    def test_local_links_excludes_web_special_and_anchors(self):
        text = (
            "[local](docs/guide.md) [web](HTTPS://example.com) "
            "[mail](mailto:test@example.com) [phone](tel:123) [section](#usage)"
        )

        self.assertEqual(
            checker.local_links(text),
            [{"label": "local", "url": "docs/guide.md"}],
        )

    @patch("markdown_link_checker.urlopen")
    def test_check_reports_success_status(self, mock_urlopen):
        response = mock_urlopen.return_value.__enter__.return_value
        response.status = 204

        self.assertEqual(
            checker.check("https://example.com", timeout=2),
            {"url": "https://example.com", "ok": True, "status": 204},
        )
        mock_urlopen.assert_called_once()
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 2)

    @patch("markdown_link_checker.urlopen")
    def test_check_reports_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError("https://example.com/missing", 404, "Not Found", {}, None)

        self.assertEqual(
            checker.check("https://example.com/missing"),
            {"url": "https://example.com/missing", "ok": False, "status": 404},
        )

    @patch("markdown_link_checker.urlopen")
    def test_check_reports_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("offline")

        result = checker.check("https://example.com")

        self.assertEqual(result["url"], "https://example.com")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "URLError")

    def test_cli_deduplicates_urls_when_checking(self):
        source = ROOT / "tests" / "_sample.md"
        source.write_text("[one](https://example.com) [two](https://example.com)", encoding="utf-8")
        try:
            with patch.object(sys, "argv", ["markdown_link_checker.py", str(source), "--check"]), patch.object(
                checker, "check", return_value={"url": "https://example.com", "ok": True, "status": 200}
            ) as mock_check, patch("sys.stdout.write") as mock_write:
                self.assertEqual(checker.main(), 0)
                self.assertEqual(mock_check.call_count, 1)
                output = "".join(call.args[0] for call in mock_write.call_args_list)
                self.assertIn("https://example.com", json.loads(output)[0]["url"])
        finally:
            source.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
