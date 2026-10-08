# short-url — Índice Mestre (Claude Code)

@AGENTS.md

O núcleo das regras chega pelos links em `.claude/rules/` (só os arquivos do núcleo; ver "Como as regras são carregadas" no `AGENTS.md`). Subagentes nativos ficam em `.claude/agents/` como symlink para `.agents/agents/<nome>/agent.md` (hoje, o `executor`; o `qa-explorer` roda só no `agy`). Skills promovidas a nativas ficam em `.claude/skills/`; skills e templates do projeto, em `.agents/skills/` e `.agents/templates/`.
