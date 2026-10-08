Subagentes deste projeto. Cada um tem pasta própria com `agent.md`, trava `PreToolUse` em Python (só biblioteca padrão, lista branca, fail-closed) e os testes da trava. Regras de uso: `.agents/rules/execution-workflow.md`.

- `executor/` — executor das tarefas dos planos (Sonnet 5.5, Claude Code). Frontmatter no formato do Claude Code, com symlink em `.claude/agents/executor.md` (o Claude Code só lê `.claude/agents/`, e carrega os agentes no início da sessão). Trava: `executor-guard.py`; testes: `python3 -I executor-guard.test.py`.
- `qa-explorer/` — QA exploratório somente leitura (Gemini 3.8 Flash, Antigravity CLI), com o navegador do Playwright MCP. O `agy` lê `.agents/agents/<nome>/agent.md` nativamente; roda com `agy --agent qa-explorer --model gemini-3.8-flash-high -p "..."` (prompt por último). Trava: `hooks.json` + `qa-guard.py`; testes: `python3 -I qa-guard.test.py`; camada B: `worktree-fingerprint.sh`.

Agente novo: siga o mesmo formato. Para o Claude Code, crie o symlink em `.claude/agents/<nome>.md` e reinicie a sessão (ou use `/agents`).
