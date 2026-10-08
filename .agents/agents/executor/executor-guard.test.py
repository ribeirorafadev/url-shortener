"""Testes de caixa-preta da trava do executor: alimentam o executor-guard.py pelo stdin, como o Claude Code faz."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).with_name("executor-guard.py")


class ExecutorGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name).resolve() / "short-url"
        (self.project / "src/domain").mkdir(parents=True)
        (self.project / "src/domain/slug.ts").write_text("export {};\n")
        (self.project / "AGENTS.md").write_text("# agentes\n")
        (self.project / "src/domain/agents-link.md").symlink_to(self.project / "AGENTS.md")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_guard(self, raw_stdin: str, with_project_dir: bool = True) -> tuple[str, str | None]:
        env = {"PATH": os.environ.get("PATH", "")}
        if with_project_dir:
            env["CLAUDE_PROJECT_DIR"] = str(self.project)
        result = subprocess.run(  # noqa: S603 — argumentos fixos, sem shell
            [sys.executable, "-I", str(GUARD)],
            input=raw_stdin,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            check=False,  # o código de saída é conferido logo abaixo
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return "pass", None
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        return output["permissionDecision"], output.get("permissionDecisionReason")

    def payload(self, tool_name: str, tool_input: dict) -> str:
        return json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "cwd": str(self.project),
                "tool_name": tool_name,
                "tool_input": tool_input,
            }
        )

    def path(self, relative: str) -> str:
        return str(self.project / relative)

    def assert_passes(self, tool_name: str, tool_input: dict) -> None:
        decision, reason = self.run_guard(self.payload(tool_name, tool_input))
        self.assertEqual(decision, "pass", reason)

    def assert_denied(self, tool_name: str, tool_input: dict) -> None:
        decision, reason = self.run_guard(self.payload(tool_name, tool_input))
        self.assertEqual(decision, "deny")
        self.assertTrue(reason)

    def assert_bash_passes(self, *commands: str) -> None:
        for command in commands:
            with self.subTest(command=command):
                self.assert_passes("Bash", {"command": command})

    def assert_bash_denied(self, *commands: str) -> None:
        for command in commands:
            with self.subTest(command=command):
                self.assert_denied("Bash", {"command": command})

    # Escrita (Write, Edit, NotebookEdit)

    def test_passes_writing_source_files(self) -> None:
        for relative in ("src/domain/slug.ts", "src/app/_lib/qr-code.ts", "prisma/schema.prisma", ".env.example"):
            with self.subTest(path=relative):
                self.assert_passes("Write", {"file_path": self.path(relative), "content": "x"})

    def test_denies_editing_tests_and_test_infrastructure(self) -> None:
        protected = (
            "src/domain/slug.test.ts",
            "src/data/prisma-link-repository.int.test.ts",
            "tests/http/redirect.http.test.ts",
            "src/components/link-card.test.tsx",
            "src/domain/link.spec.ts",
            "src/domain/__fakes__/in-memory-link-repository.ts",
            "vitest.config.mts",
            "vitest.http.config.mts",
        )
        for relative in protected:
            for tool in ("Write", "Edit"):
                with self.subTest(path=relative, tool=tool):
                    self.assert_denied(tool, {"file_path": self.path(relative), "old_string": "a", "new_string": "b"})

    def test_denies_editing_harness_and_documentation(self) -> None:
        protected = (
            ".agents/rules/execution-workflow.md",
            "docs/superpowers/specs/2026-10-07-short-url-mvp-design.md",
            "AGENTS.md",
            "CLAUDE.md",
            "HANDOFF.md",
            ".claude/agents/executor.md",
            ".claude/settings.json",
            ".git/hooks/pre-commit",
            ".gitignore",
        )
        for relative in protected:
            with self.subTest(path=relative):
                self.assert_denied("Write", {"file_path": self.path(relative), "content": "x"})

    def test_denies_editing_dependency_manifests(self) -> None:
        for relative in ("package.json", "package-lock.json", ".npmrc"):
            with self.subTest(path=relative):
                self.assert_denied("Edit", {"file_path": self.path(relative), "old_string": "a", "new_string": "b"})

    def test_denies_editing_env_files(self) -> None:
        for relative in (".env", ".env.local", ".env.development.local"):
            with self.subTest(path=relative):
                self.assert_denied("Write", {"file_path": self.path(relative), "content": "x"})

    def test_denies_writing_outside_the_project(self) -> None:
        for raw in ("/opt/evil.ts", str(self.project / ".." / "outside.ts")):
            with self.subTest(path=raw):
                self.assert_denied("Write", {"file_path": raw, "content": "x"})

    def test_denies_writing_through_symlink_to_protected_file(self) -> None:
        self.assert_denied("Write", {"file_path": self.path("src/domain/agents-link.md"), "content": "x"})

    def test_denies_notebook_edit_on_protected_path(self) -> None:
        self.assert_denied("NotebookEdit", {"notebook_path": self.path("docs/x.ipynb"), "new_source": "x"})

    # Leitura (Read, Grep, Glob)

    def test_passes_reading_tests_spec_and_rules(self) -> None:
        for relative in ("src/domain/slug.test.ts", "docs/superpowers/specs/x.md", ".agents/rules/code-style.md", ".env.example"):
            with self.subTest(path=relative):
                self.assert_passes("Read", {"file_path": self.path(relative)})

    def test_denies_reading_secrets(self) -> None:
        for relative in (".env", ".env.development.local", "certs/server.pem", "certs/server.key"):
            with self.subTest(path=relative):
                self.assert_denied("Read", {"file_path": self.path(relative)})

    def test_denies_reading_outside_the_project(self) -> None:
        self.assert_denied("Read", {"file_path": "/etc/passwd"})

    def test_passes_searching_inside_the_project(self) -> None:
        self.assert_passes("Grep", {"pattern": "generateSlug", "path": self.path("src")})
        self.assert_passes("Grep", {"pattern": "generateSlug"})
        self.assert_passes("Glob", {"pattern": "src/**/*.ts"})

    def test_denies_searching_secrets_or_outside_the_project(self) -> None:
        self.assert_denied("Grep", {"pattern": "DATABASE", "path": self.path(".env.development.local")})
        self.assert_denied("Grep", {"pattern": "DATABASE", "glob": ".env*"})
        self.assert_denied("Grep", {"pattern": "root", "path": "/etc"})
        self.assert_denied("Glob", {"pattern": "**/*", "path": "/home"})

    # Bash

    def test_passes_test_lint_and_typecheck_commands(self) -> None:
        self.assert_bash_passes(
            "npm test",
            "npm run lint",
            "npm run typecheck",
            "npm run test:http",
            "npx vitest run src/domain/slug.test.ts",
            "npx tsc --noEmit",
            "npx prisma generate",
            "npx prisma validate",
            "npm test 2>&1 | tail -40",
            "npx vitest run > /dev/null",
            "DATABASE_URL=postgresql://127.0.0.1:5432/shorturl_test npx vitest run",
        )

    def test_passes_read_only_git_and_shell_commands(self) -> None:
        self.assert_bash_passes(
            "git status",
            "git diff --stat",
            "git --no-pager log --oneline -5",
            "git -C src diff",
            "git show HEAD:src/domain/slug.ts",
            "ls -la src/domain",
            "cat src/domain/slug.test.ts",
            "grep -rn generateSlug src",
            "find src -name '*.ts'",
            "wc -l src/domain/slug.ts && head -20 src/domain/slug.ts",
            "mkdir -p src/domain/ports",
        )

    def test_passes_formatting_own_source_files(self) -> None:
        self.assert_bash_passes(
            "npx prettier --write src/domain/slug.ts",
            "npx eslint --fix src/domain/slug.ts",
        )

    def test_denies_git_commands_that_write(self) -> None:
        self.assert_bash_denied(
            "git commit -m 'feat: x'",
            "git push",
            "git -C . commit -am x",
            "git add .",
            "git checkout -- src/domain/slug.test.ts",
            "git restore src",
            "git reset --hard",
            "git stash",
            "git clean -fd",
            "git -c core.pager=sh log",
            "git diff --output=src/domain/slug.test.ts",
            "npm test && git commit -m x",
        )

    def test_denies_dependency_changes(self) -> None:
        self.assert_bash_denied(
            "npm install",
            "npm i zod",
            "npm install --save-dev vitest",
            "npm uninstall qrcode",
            "npm update",
            "npx some-random-package",
            "npx -p left-pad node",
            "npx prisma migrate reset",
            "npx prisma db push --force-reset",
        )

    def test_denies_reading_env_files_through_the_shell(self) -> None:
        self.assert_bash_denied(
            "cat .env.development.local",
            "head -5 .env",
            "grep DATABASE .env*",
        )

    def test_denies_reading_outside_the_project_through_the_shell(self) -> None:
        self.assert_bash_denied(
            "cat ~/.ssh/id_ed25519",
            "tail ~/.npmrc",
            "cat /etc/passwd",
            "ls /home",
            "git -C /etc log",
        )

    def test_passes_patterns_that_only_look_like_absolute_paths(self) -> None:
        self.assert_bash_passes("grep -rn '/api/links' src", "cat /dev/null")

    def test_denies_shell_writes_to_protected_paths(self) -> None:
        self.assert_bash_denied(
            "echo x > src/domain/slug.test.ts",
            "echo x >> AGENTS.md",
            "cat src/domain/slug.ts > package.json",
            "rm src/domain/slug.test.ts",
            "mv src/domain/slug.ts src/domain/slug.test.ts",
            "cp /tmp/x .npmrc",
            "touch docs/x.md",
            "mkdir .agents/novo",
            "npx vitest run -u",
            "npx vitest run --update",
        )

    def test_denies_shell_writes_with_wide_reach(self) -> None:
        self.assert_bash_denied(
            "rm -rf src",
            "rm -r src/domain",
            "rm src/domain/*.ts",
            "rm src",
            "npx prettier --write .",
            "npx eslint --fix src",
            "npm run lint -- --fix",
            "find . -name '*.ts' -delete",
            "find . -exec rm {} ;",
            "rg --pre cat foo",
            "sort -o src/domain/slug.ts src/domain/slug.ts",
        )

    def test_denies_flags_that_write_files(self) -> None:
        self.assert_bash_denied(
            "npx eslint -o docs/report.txt src/domain/slug.ts",
            "npx vitest run --outputFile=AGENTS.md",
            "npx tsc --outDir docs",
            "cp --target-directory=docs src/domain/slug.ts",
            "mv --target-directory=.agents src/domain/slug.ts",
        )

    def test_denies_relative_paths_that_escape_the_project(self) -> None:
        self.assert_bash_denied("cat ../outside.txt", "ls ../..")
        self.assert_denied("Glob", {"pattern": "../**/*"})
        self.assert_denied("Read", {"file_path": self.path("../outside.txt")})

    def test_denies_commands_outside_the_whitelist(self) -> None:
        self.assert_bash_denied(
            "sed -i s/a/b/ src/domain/slug.ts",
            "node -e \"require('fs').writeFileSync('AGENTS.md', '')\"",
            "python3 -c 'print(1)'",
            "bash -c 'git commit'",
            "sh -c ls",
            "curl https://example.com",
            "sudo ls",
            "cd src && ls",
            "xargs rm < lista.txt",
            "docker compose down -v",
        )

    def test_denies_shell_tricks_that_hide_the_real_command(self) -> None:
        self.assert_bash_denied(
            "echo $(cat .env)",
            "echo `git push`",
            "cat $HOME/.ssh/id_ed25519",
            "ls\ngit push",
            "npm test &",
            "cat <(git push)",
            "echo 'sem fim",
        )

    # Outras ferramentas e entrada malformada

    def test_passes_delivering_the_final_report(self) -> None:
        # No auto mode, o subagente entrega o relatório por esta ferramenta; negá-la some com o relatório.
        self.assert_passes("SubagentHandback", {"report": "STATUS: VERDE"})

    def test_denies_tools_outside_the_whitelist(self) -> None:
        for tool in ("WebFetch", "WebSearch", "Agent", "Skill", "mcp__github__push_files", "PowerShell"):
            with self.subTest(tool=tool):
                self.assert_denied(tool, {"url": "https://example.com"})

    def test_fails_closed_on_malformed_input(self) -> None:
        for raw in ("", "not json", "[]", json.dumps({"tool_name": 7}), json.dumps({"tool_name": "Write", "tool_input": "x"})):
            with self.subTest(raw=raw):
                decision, _ = self.run_guard(raw)
                self.assertEqual(decision, "deny")

    def test_fails_closed_without_project_dir(self) -> None:
        decision, _ = self.run_guard(self.payload("Read", {"file_path": self.path("src/domain/slug.ts")}), with_project_dir=False)
        self.assertEqual(decision, "deny")


if __name__ == "__main__":
    unittest.main(verbosity=1)
