Subagentes deste projeto. Cada um: pasta própria com agent.md (frontmatter name+description compatível com o formato nativo do Claude Code).

Pra funcionar nativamente (Task tool, tools/model/permissionMode restritos, contexto isolado), copie ou symlink agent.md pra .claude/agents/<nome>.md e confira com /context. Sem isso é só texto colado via @import.

O Antigravity também lê `.agents/agents/<nome>.md` (ou `<nome>/agent.md`) nativamente, com frontmatter próprio (`name`, `description`, `tools`, `model`). Neste projeto, o primeiro agente previsto é o revisor de fatias, em discussão como pendência primária (ver `HANDOFF.md`, "Pendência primária").
