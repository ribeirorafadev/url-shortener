# Convenções de Código — short-url

## Formatação
- Linter/formatter: ESLint + Prettier, que é o padrão global do autor para JS/TS. O lint roda no CI a cada push (ver `architecture.md`, "CI no MVP"). As regras exatas e um eventual hook de pre-commit ficam para o setup.
  - O ESLint do Next (`eslint-config-next`) depende do `typescript-eslint`, que exige TypeScript `<6.1.0`. Por isso o projeto usa o TS 6.0.3 (ver `architecture.md`).
  - Regra `import/no-extraneous-dependencies: error`. O plugin `eslint-plugin-import` já vem com o `eslint-config-next`. Ela barra a dependência fantasma: todo pacote importado precisa estar declarado no `package.json`.
  - Candidata a definir na spec: regra `no-restricted-imports` para barrar `next/*`, `@/data/*` e `@/infra/*` dentro de `src/domain/` e transformar o AD-004 em erro de lint.
- Indentação: ver `.editorconfig` (gerado automaticamente — não duplicar valor aqui)

## Nomenclatura
- Identificadores: `camelCase` para variáveis e funções; `PascalCase` para classes, tipos, interfaces e componentes React.
- Os nomes revelam a intenção de negócio: `calculateExpirationDate`, nunca `calcExp`.
- Arquivos: **kebab-case em tudo** (decidido em 2026-09-28): `link-service.ts`, `prisma-link-repository.ts`, `link-card.tsx`. Os nomes de rota do Next.js são fixos (`page.tsx`, `route.ts`, `layout.tsx`). Os identificadores dentro do arquivo seguem as regras acima (`LinkService`, `createLink`).
  - Motivos: é o padrão do shadcn/ui (`components/ui/dropdown-menu.tsx`) e das rotas do Next. Também elimina bugs de caixa: macOS e Windows não diferenciam `LinkService.ts` de `linkService.ts`, e o Git nesses sistemas (`core.ignorecase=true`) não registra renomeações só de caixa, mas o Linux da Vercel diferencia, e o import falha no deploy com `Module not found`.
  - Descartados: PascalCase para classes e componentes (mistura com os arquivos do shadcn e mantém o risco de caixa) e PascalCase em tudo, no estilo Java (destoa do ecossistema).
- Comentários: curtos, só em lógica de negócio não óbvia ou em decisão não trivial.

## Padrões de commit
Decidido em 2026-09-28.
- **Formato:** [Conventional Commits 1.0.0](https://www.conventionalcommits.org/pt-br/v1.0.0/), `tipo(escopo): descrição`. **Tipo e escopo em inglês** (palavras-chave da especificação), **descrição em pt-BR**, no imperativo e curta. Mudança incompatível leva `!` (`feat(data)!: ...`).
  - Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`.
  - Escopos sugeridos: `domain`, `data`, `app`, `redirect`, `create`, `manage`, `spec`, `deps`.
  - Exemplos: `feat(domain): gera slug base62 com CSPRNG`, `fix(redirect): responde 410 para link desativado`, `chore(deps): fixa prisma em 7.10.0`.
- **Sem validação automática** (projeto solo). Evolução possível: hook `commit-msg` em shell em `.githooks/` com `core.hooksPath`, sem dependência. commitlint + husky foram descartados por adicionarem dependências.
- **Trailer `Co-Authored-By` do Claude mantido** nos commits feitos pelo agente. É uma escolha de transparência: o desenvolvimento é guiado por IA.
- **Branches e fatias (decidido em 2026-10-01):** `main` sempre "deployável". O MVP tem **uma spec e três fatias**, e cada fatia tem **plano, branch e PR próprios**:
  1. `feat/mvp-1-base`: setup, Docker, CI, ruleset, Vercel, Neon e o domínio com testes;
  2. `feat/mvp-2-create-redirect`: criação (Google Safe Browsing e rate limit), redirect, teste de concorrência e testes HTTP;
  3. `feat/mvp-3-manage`: página de gestão (estatísticas, QR, desativar) e README.
  - Cada fatia termina com o site funcionando e publicado. A fatia seguinte nasce da `main` atualizada, depois do merge da anterior.
  - Na spec, o campo **Branch Alvo** lista as três branches; cada plano usa a da sua fatia em **Branch de Trabalho**.
  - A spec e os planos são documentação e vão direto na `main`, porque o ruleset só é ativado durante a fatia 1.
  - Push só com autorização do Rafael.
  - Motivos: PRs menores, que dá para revisar de verdade; a primeira PR, feita em conjunto, acontece no começo da semana e não no fim; e sempre existe uma versão no ar se o prazo apertar.
  - Descartado: uma branch `feat/mvp` com um PR só no fim, grande demais para revisar e sem nada no ar até o último dia.
- **Pull Requests (decidido em 2026-09-30):** o código entra na `main` só por PR com o CI verde, porque o ruleset da `main` barra o merge com ✗ (ver `architecture.md`, "Publicação só com o CI verde"). O ruleset exige **só o CI verde, sem aprovação de revisor**: o GitHub não deixa o autor aprovar o próprio PR, e o projeto é solo. A revisão é o Rafael ler o diff ("Files changed") antes do merge. O título do PR segue o mesmo formato de Conventional Commits. O ruleset é ativado na fatia 1, junto com o CI; até lá, os commits de documentação (design, spec e planos) vão direto na `main`. Cada fatia gera **um PR**.

