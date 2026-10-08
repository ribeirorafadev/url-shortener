"""Trava PreToolUse do executor Sonnet (D4, execution-workflow.md).

Lista branca e fail-closed. O executor só escreve código de produção dentro do
projeto: testes, harness, documentação, manifestos de dependência e `.env*` ficam
fora do alcance, e o Bash só aceita comandos conhecidos. Protege contra engano,
não contra má-fé; contra isso valem a revisão do Opus e o CI.
"""

import json
import os
import re
import shlex
import sys
from pathlib import Path

# SubagentHandback só entrega o relatório final (auto mode); sem ela, o relatório se perde.
REPORT_TOOLS = frozenset({"SubagentHandback"})
ALLOWED_TOOLS = frozenset({"Read", "Grep", "Glob", "Edit", "Write", "NotebookEdit", "Bash"}) | REPORT_TOOLS
WRITE_TOOL_PATH_KEYS = {"Write": "file_path", "Edit": "file_path", "NotebookEdit": "notebook_path"}

PROTECTED_TOP_DIRS = frozenset({".agents", "docs", ".claude", ".git"})
PROTECTED_ROOT_FILES = frozenset(
    {"AGENTS.md", "CLAUDE.md", "HANDOFF.md", "package.json", "package-lock.json", "npm-shrinkwrap.json", ".npmrc", ".gitignore"}
)
TEST_DIR_NAMES = frozenset({"tests", "__tests__", "__fakes__"})
TEST_FILE_PATTERN = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$")
SECRET_SUFFIXES = frozenset({".pem", ".key"})

COMMAND_SEPARATORS = frozenset({"&&", "||", ";", "|"})
REDIRECTIONS = frozenset({">", ">>", ">|", "&>", "&>>", ">&", "<", "<<", "<<<", "<>"})
SHELL_TRICKS = ("$", "`", "<(", ">(", "\n", "\r")
GLOB_CHARS = frozenset("*?[")
ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

READ_ONLY_PROGRAMS = frozenset(
    {"ls", "cat", "head", "tail", "wc", "grep", "rg", "diff", "pwd", "echo", "cut", "sort", "stat", "file", "which", "true"}
)
# Flags que fazem um programa "só de leitura" escrever arquivo ou rodar outro programa.
WRITING_FLAGS = {"sort": ("-o", "--output"), "rg": ("--pre",)}
FIND_ACTIONS = frozenset({"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprint0", "-fprintf", "-fls"})
GIT_READ_ONLY = frozenset({"status", "diff", "log", "show", "ls-files", "rev-parse", "blame", "grep"})
GIT_SAFE_GLOBAL_FLAGS = frozenset({"--no-pager", "--no-optional-locks", "-P"})
NPM_ALLOWED = frozenset({"test", "t", "run", "run-script", "ls", "ci"})
NPX_TOOLS = frozenset({"vitest", "tsc", "eslint", "prettier", "prisma", "next"})
PRISMA_DESTRUCTIVE = frozenset({"reset", "--force-reset", "--accept-data-loss", "execute"})
VITEST_SNAPSHOT_UPDATE = frozenset({"-u", "--update"})
FORMATTER_WRITE_FLAGS = frozenset({"--write", "-w", "--fix"})
# eslint -o, vitest --outputFile, tsc --outDir: escrevem arquivo fora do controle da trava.
NPX_OUTPUT_FLAG_PREFIXES = ("--output", "--outDir", "--outFile", "--out-dir", "--out-file")


class Denied(Exception):
    pass


def deny_output(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Bloqueado pela trava do executor: {reason}. Não contorne; registre no relatório final para o Opus."
            ),
        }
    }


def project_root() -> Path:
    raw = os.environ.get("CLAUDE_PROJECT_DIR")
    if not raw:
        raise Denied("CLAUDE_PROJECT_DIR ausente")
    return Path(raw).resolve()


def resolve_in_project(raw: object, base: Path, root: Path) -> Path:
    if not isinstance(raw, str) or not raw:
        raise Denied("caminho ausente")
    path = Path(raw)
    resolved = (path if path.is_absolute() else base / path).resolve()
    if not resolved.is_relative_to(root):
        raise Denied(f"{raw} fica fora do projeto")
    return resolved


def is_secret_name(name: str) -> bool:
    return (name.startswith(".env") and name != ".env.example") or Path(name).suffix in SECRET_SUFFIXES


def write_protection(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    if not parts:
        return "a raiz do projeto não é alvo de escrita"
    name = parts[-1]
    if parts[0] in PROTECTED_TOP_DIRS:
        return f"{parts[0]}/ é do harness, da documentação ou do Git"
    if len(parts) == 1 and name in PROTECTED_ROOT_FILES:
        return f"{name} é protegido (dependência nova ou regra só pelo Opus)"
    if any(part in TEST_DIR_NAMES for part in parts) or TEST_FILE_PATTERN.search(name) or name.startswith("vitest."):
        return f"{name} é teste ou infraestrutura de teste, que é do Opus (D1)"
    if is_secret_name(name):
        return f"{name} guarda segredo"
    return None


def ensure_writable(raw: object, base: Path, root: Path) -> Path:
    path = resolve_in_project(raw, base, root)
    reason = write_protection(path, root)
    if reason:
        raise Denied(reason)
    return path


def ensure_readable(raw: object, base: Path, root: Path) -> None:
    path = resolve_in_project(raw, base, root)
    if is_secret_name(path.name):
        raise Denied(f"{path.name} guarda segredo")


def judge_search(tool_name: str, tool_input: dict, base: Path, root: Path) -> None:
    if tool_input.get("path") is not None:
        ensure_readable(tool_input["path"], base, root)
    glob = tool_input.get("glob")
    if isinstance(glob, str) and ".env" in glob:
        raise Denied("busca em arquivos .env")
    pattern = tool_input.get("pattern")
    if tool_name == "Glob" and isinstance(pattern, str) and ".." in Path(pattern).parts:
        raise Denied("padrão do Glob com .. sai do projeto")
    if tool_name == "Glob" and isinstance(pattern, str) and pattern.startswith(("/", "~")):
        resolve_in_project(pattern.split("*", 1)[0] or "/", base, root)


def split_segments(command: str) -> list[list[str]]:
    for trick in SHELL_TRICKS:
        if trick in command:
            raise Denied(f"o comando usa {trick!r} (expansão, subshell ou várias linhas); rode um comando simples por vez")
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        words = list(lexer)
    except ValueError as error:
        raise Denied(f"comando malformado ({error})") from error

    segments: list[list[str]] = [[]]
    index = 0
    while index < len(words):
        word = words[index]
        if word in COMMAND_SEPARATORS:
            segments.append([])
        elif word in REDIRECTIONS:
            target = words[index + 1] if index + 1 < len(words) else ""
            fd_duplication = word == ">&" and target.isdigit()
            if not (fd_duplication or (word in (">", ">>", "&>") and target == "/dev/null")):
                raise Denied("redirecionamento só para /dev/null; para escrever arquivo use Write ou Edit")
            if segments[-1] and segments[-1][-1].isdigit():
                segments[-1].pop()  # o "2" de "2>&1" é descritor, não argumento
            index += 1
        elif word in ("&", "(", ")") or set(word) <= set("&|;<>()"):
            raise Denied(f"operador {word!r} não é aceito")
        else:
            segments[-1].append(word)
        index += 1
    return segments


def positional(args: list[str]) -> list[str]:
    return [arg for arg in args if not arg.startswith("-")]


def ensure_precise_writes(args: list[str], base: Path, root: Path) -> None:
    targets = positional(args)
    if not targets:
        raise Denied("escrita sem arquivo explícito alcança o projeto inteiro")
    for target in targets:
        if GLOB_CHARS & set(target):
            raise Denied(f"{target} usa curinga; nomeie cada arquivo")
        path = ensure_writable(target, base, root)
        if path.is_dir():
            raise Denied(f"{target} é diretório; nomeie cada arquivo")


def judge_git(args: list[str]) -> None:
    index = 0
    while index < len(args) and args[index].startswith("-"):
        if args[index] == "-C":
            index += 2
        elif args[index] in GIT_SAFE_GLOBAL_FLAGS:
            index += 1
        else:
            raise Denied(f"opção global do git {args[index]} não é aceita")
    subcommand = args[index] if index < len(args) else ""
    if subcommand not in GIT_READ_ONLY:
        raise Denied(f"git {subcommand} escreve no repositório; o executor só lê o Git (commit e push são do Opus)")
    if any(arg.startswith("--output") for arg in args):
        raise Denied("git com --output escreve arquivo")


def judge_npx(args: list[str], base: Path, root: Path) -> None:
    if not args or args[0].startswith("-") or args[0] not in NPX_TOOLS:
        raise Denied(f"npx só roda {', '.join(sorted(NPX_TOOLS))}; dependência nova é do Opus")
    tool, tool_args = args[0], args[1:]
    if any(arg == "-o" or arg.startswith(NPX_OUTPUT_FLAG_PREFIXES) for arg in tool_args):
        raise Denied(f"{tool} com opção de saída escreve arquivo")
    if tool == "prisma" and PRISMA_DESTRUCTIVE & set(tool_args):
        raise Denied("comando do Prisma que apaga dados ou roda SQL solto")
    if tool == "vitest" and VITEST_SNAPSHOT_UPDATE & set(tool_args):
        raise Denied("atualizar snapshot reescreve teste, que é do Opus (D1)")
    if tool in ("prettier", "eslint") and FORMATTER_WRITE_FLAGS & set(tool_args):
        ensure_precise_writes([arg for arg in tool_args if arg not in FORMATTER_WRITE_FLAGS], base, root)


def judge_segment(tokens: list[str], base: Path, root: Path) -> None:
    while tokens and ENV_ASSIGNMENT.match(tokens[0]):
        tokens = tokens[1:]
    if not tokens:
        raise Denied("comando vazio")
    program, args = tokens[0], tokens[1:]
    for arg in tokens:
        value = arg.split("=")[-1]
        if is_secret_name(Path(value).name):
            raise Denied(f"{arg} aponta para arquivo com segredo")
        if value.startswith("~"):
            raise Denied(f"{arg} aponta para fora do projeto")
        if ".." in Path(value).parts:
            resolve_in_project(value, base, root)
        # Só caminho absoluto que existe: "/api/links" num grep é padrão, não arquivo.
        if value.startswith("/") and value != "/dev/null" and Path(value).exists():
            resolve_in_project(value, base, root)

    if program in READ_ONLY_PROGRAMS:
        if any(arg.startswith(flag) for flag in WRITING_FLAGS.get(program, ()) for arg in args):
            raise Denied(f"{program} com essa opção escreve arquivo ou roda outro programa")
    elif program == "find":
        if FIND_ACTIONS & set(args):
            raise Denied("find com ação (-exec, -delete) não é aceito")
    elif program == "git":
        judge_git(args)
    elif program == "npm":
        subcommand = args[0] if args else ""
        if subcommand not in NPM_ALLOWED:
            raise Denied(f"npm {subcommand} não é aceito; dependência nova é do Opus")
        if FORMATTER_WRITE_FLAGS & set(args):
            raise Denied("formatação com escrita só com npx e arquivos explícitos")
    elif program == "npx":
        judge_npx(args, base, root)
    elif program in ("mkdir", "touch", "mv", "cp"):
        option_values = [arg.split("=", 1)[1] for arg in args if arg.startswith("--") and "=" in arg]
        for target in positional(args) + option_values:
            ensure_writable(target, base, root)
    elif program == "rm":
        if any(arg == "--recursive" or (arg.startswith("-") and not arg.startswith("--") and set(arg) & set("rR")) for arg in args):
            raise Denied("rm recursivo não é aceito")
        ensure_precise_writes(args, base, root)
    else:
        raise Denied(f"o programa {program} não está na lista branca")


def judge_bash(tool_input: dict, base: Path, root: Path) -> None:
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        raise Denied("comando ausente")
    for segment in split_segments(command):
        judge_segment(segment, base, root)


def judge(payload: object) -> None:
    if not isinstance(payload, dict):
        raise Denied("entrada malformada")
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        raise Denied("entrada sem tool_name ou tool_input")
    if tool_name not in ALLOWED_TOOLS:
        raise Denied(f"a ferramenta {tool_name} não está na lista branca")
    if tool_name in REPORT_TOOLS:
        return
    root = project_root()
    cwd = payload.get("cwd")
    base = Path(cwd).resolve() if isinstance(cwd, str) and cwd else root

    if tool_name in WRITE_TOOL_PATH_KEYS:
        ensure_writable(tool_input.get(WRITE_TOOL_PATH_KEYS[tool_name]), base, root)
    elif tool_name == "Read":
        ensure_readable(tool_input.get("file_path"), base, root)
    elif tool_name in ("Grep", "Glob"):
        judge_search(tool_name, tool_input, base, root)
    else:
        judge_bash(tool_input, base, root)


def main() -> None:
    try:
        judge(json.loads(sys.stdin.read()))
    except Denied as denied:
        print(json.dumps(deny_output(str(denied)), ensure_ascii=False))
    except Exception as error:  # noqa: BLE001 — fail-closed: erro na trava nunca libera a ferramenta
        print(json.dumps(deny_output(f"erro na trava ({type(error).__name__})"), ensure_ascii=False))


if __name__ == "__main__":
    main()
