"""Trava PreToolUse do agente de QA do agy (D6c, execution-workflow.md).

Lista branca e fail-closed: só passa ler os schemas do Playwright e usar o
navegador contra a aplicação local. Qualquer outra coisa, inclusive entrada
malformada ou erro inesperado, vira "deny".
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA_DIR = (Path.home() / ".gemini/antigravity-cli/mcp/playwright").resolve()
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
BROWSER_SERVER = "playwright"
# browser_run_code_unsafe roda Node no servidor MCP e browser_file_upload lê arquivos locais: os dois alcançam o disco.
FILESYSTEM_TOOLS = frozenset({"browser_run_code_unsafe", "browser_file_upload"})


def allow() -> dict:
    return {"decision": "allow"}


def deny(reason: str) -> dict:
    return {"decision": "deny", "reason": f"Bloqueado pela trava do QA: {reason}. O QA só lê e usa o navegador."}


def is_local_app_url(url: object) -> bool:
    if not isinstance(url, str):
        return False
    parts = urlsplit(url)
    # O "@" cobre credenciais embutidas, como http://127.0.0.1@evil.com/.
    return parts.scheme in ("http", "https") and "@" not in parts.netloc and parts.hostname in LOCAL_HOSTS


def judge_view_file(args: dict) -> dict:
    raw_path = args.get("AbsolutePath")
    if not isinstance(raw_path, str) or not raw_path:
        return deny("view_file sem caminho")
    path = Path(raw_path).resolve()
    if path.parent != SCHEMA_DIR or path.suffix != ".json":
        return deny("view_file só lê os schemas do Playwright")
    return allow()


def judge_mcp_call(args: dict) -> dict:
    if args.get("ServerName") != BROWSER_SERVER:
        return deny("só o MCP do navegador (playwright) é liberado")
    tool_name = args.get("ToolName")
    if not isinstance(tool_name, str) or not tool_name.startswith("browser_"):
        return deny("ferramenta do playwright inválida")
    if tool_name in FILESYSTEM_TOOLS:
        return deny(f"{tool_name} alcança o sistema de arquivos")
    arguments = args.get("Arguments") or {}
    if not isinstance(arguments, dict):
        return deny("argumentos malformados")
    must_have_url = tool_name == "browser_navigate"
    if (must_have_url or "url" in arguments) and not is_local_app_url(arguments.get("url")):
        return deny("o navegador só abre a aplicação local (localhost, 127.0.0.1, [::1])")
    return allow()


def judge(payload: object) -> dict:
    if not isinstance(payload, dict):
        return deny("entrada malformada")
    tool_call = payload.get("toolCall")
    if not isinstance(tool_call, dict) or not isinstance(tool_call.get("name"), str):
        return deny("entrada sem toolCall")
    args = tool_call.get("args") or {}
    if not isinstance(args, dict):
        return deny("argumentos malformados")
    name = tool_call["name"]
    if name == "view_file":
        return judge_view_file(args)
    if name == "call_mcp_tool":
        return judge_mcp_call(args)
    return deny(f"a ferramenta {name} não está na lista branca")


def main() -> None:
    try:
        verdict = judge(json.loads(sys.stdin.read()))
    except Exception as error:  # noqa: BLE001 — fail-closed: erro na trava nunca libera a ferramenta
        verdict = deny(f"erro na trava ({type(error).__name__})")
    print(json.dumps(verdict, ensure_ascii=False))


if __name__ == "__main__":
    main()
