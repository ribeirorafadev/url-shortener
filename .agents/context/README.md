Contexto de domínio do projeto (regras de negócio, fluxos, schema de dados, mapa de erros). Um arquivo por assunto, cada um com no máximo 12 mil caracteres. O glossário fica no `AGENTS.md`.

Estes arquivos **não são carregados automaticamente**: o índice do `AGENTS.md` diz quando ler cada um. Trechos marcados **[→ spec]** são detalhe de implementação e vão para a spec do MVP quando ela for escrita (decisão de 2026-10-03).

| Arquivo | Assunto |
|---|---|
| `url-validation.md` | validação da URL de destino (R1 a R7), IDN |
| `link-lifecycle.md` | slug, colisão, limite de cliques, expiração |
| `link-creation.md` | token na criação, contrato `createLink`, card, QR, fluxo de criação |
| `redirect.md` | pré-validação do slug, respostas, UPDATE atômico, clique, bots, `HEAD`, fluxo do redirect |
| `manage-page.md` | página de gestão, desativação, fluxo de gestão |
| `data-model.md` | modelo de dados |
| `error-map.md` | mapa de erros |
