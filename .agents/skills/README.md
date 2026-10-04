Skills específicas deste projeto. Cada skill: pasta com SKILL.md (formato oficial Claude Code — funciona também como doc pra outros agentes).

Pra funcionar nativamente no Claude Code (auto-invocação por description), copie ou symlink a pasta pra .claude/skills/<nome>/ e confira com /context se foi carregada. Sem isso, a skill só entra em contexto se referenciada manualmente no `AGENTS.md`. O Antigravity lê `.agents/skills/` nativamente. Neste projeto, skills nascem durante as fatias, só quando uma tarefa ou um erro se repetir (harness, etapa 2; ver `HANDOFF.md`).
