"""Testes de caixa-preta da trava do QA: alimentam o qa-guard.py pelo stdin, como o agy faz."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).with_name("qa-guard.py")
SCHEMA_DIR = Path.home() / ".gemini/antigravity-cli/mcp/playwright"
PROJECT_ROOT = GUARD.resolve().parents[3]


def run_guard(raw_stdin: str) -> dict:
    result = subprocess.run(  # noqa: S603 — argumentos fixos, sem shell
        [sys.executable, "-I", str(GUARD)],
        input=raw_stdin,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,  # a trava nega pelo stdout, não pelo código de saída
    )
    if result.returncode != 0:
        raise AssertionError(f"a trava saiu com {result.returncode}: {result.stderr}")
    return json.loads(result.stdout)


def tool_call(name: str, args: dict) -> str:
    return json.dumps({"stepIdx": 1, "toolCall": {"name": name, "args": args}})


def mcp_call(tool_name: str, arguments: dict | None = None, server: str = "playwright") -> str:
    return tool_call(
        "call_mcp_tool",
        {"ServerName": server, "ToolName": tool_name, "Arguments": arguments or {}},
    )


class QaGuardTest(unittest.TestCase):
    def assert_decision(self, raw_stdin: str, expected: str) -> None:
        self.assertEqual(run_guard(raw_stdin)["decision"], expected)

    def test_allows_reading_playwright_tool_schemas(self) -> None:
        schema = str(SCHEMA_DIR / "browser_navigate.json")
        self.assert_decision(tool_call("view_file", {"AbsolutePath": schema}), "allow")

    def test_denies_reading_project_files_and_secrets(self) -> None:
        for path in (str(PROJECT_ROOT / ".env.development.local"), "/etc/passwd"):
            with self.subTest(path=path):
                self.assert_decision(tool_call("view_file", {"AbsolutePath": path}), "deny")

    def test_denies_path_traversal_out_of_schema_dir(self) -> None:
        escaped = str(SCHEMA_DIR / ".." / ".." / "settings.json")
        self.assert_decision(tool_call("view_file", {"AbsolutePath": escaped}), "deny")

    def test_denies_non_json_file_inside_schema_dir(self) -> None:
        self.assert_decision(tool_call("view_file", {"AbsolutePath": str(SCHEMA_DIR / "notes.txt")}), "deny")

    def test_allows_navigation_to_local_app(self) -> None:
        for url in ("http://localhost:3000/", "http://127.0.0.1:3000/aB3xZ9k", "http://[::1]:3000/"):
            with self.subTest(url=url):
                self.assert_decision(mcp_call("browser_navigate", {"url": url}), "allow")

    def test_denies_navigation_outside_local_app(self) -> None:
        urls = (
            "https://example.com/",
            "http://localhost.evil.com/",
            "http://127.0.0.1@evil.com/",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assert_decision(mcp_call("browser_navigate", {"url": url}), "deny")

    def test_denies_navigation_without_url(self) -> None:
        self.assert_decision(mcp_call("browser_navigate", {"href": "https://example.com/"}), "deny")

    def test_denies_opening_external_tab(self) -> None:
        self.assert_decision(mcp_call("browser_tabs", {"action": "new", "url": "https://example.com/"}), "deny")

    def test_allows_regular_browser_interaction(self) -> None:
        for tool_name in ("browser_snapshot", "browser_click", "browser_type", "browser_evaluate", "browser_network_requests"):
            with self.subTest(tool=tool_name):
                self.assert_decision(mcp_call(tool_name, {"element": "x"}), "allow")

    def test_denies_tools_that_reach_the_filesystem(self) -> None:
        for tool_name in ("browser_run_code_unsafe", "browser_file_upload"):
            with self.subTest(tool=tool_name):
                self.assert_decision(mcp_call(tool_name, {"code": "require('fs')"}), "deny")

    def test_denies_other_mcp_servers(self) -> None:
        self.assert_decision(mcp_call("query-docs", server="context7"), "deny")

    def test_denies_every_tool_outside_the_whitelist(self) -> None:
        for name in ("write_to_file", "replace_file_content", "run_command", "read_resource", "manage_task"):
            with self.subTest(tool=name):
                self.assert_decision(tool_call(name, {"TargetFile": "x"}), "deny")

    def test_fails_closed_on_malformed_input(self) -> None:
        for raw in ("", "not json", "[]", json.dumps({"toolCall": None}), json.dumps({"toolCall": {"name": 7}})):
            with self.subTest(raw=raw):
                self.assert_decision(raw, "deny")

    def test_deny_always_explains_the_reason(self) -> None:
        verdict = run_guard(tool_call("write_to_file", {}))
        self.assertTrue(verdict.get("reason"))


if __name__ == "__main__":
    os.chdir(GUARD.parent)
    unittest.main(verbosity=1)
