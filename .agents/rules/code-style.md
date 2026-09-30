# Convenções de Código — short-url

## Formatação
- Linter/formatter: ESLint + Prettier, que é o padrão global do autor para JS/TS. Configuração exata (regras, execução em pre-commit ou só no CI) a definir no setup.
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
- **Branches:** `main` sempre "deployável"; cada spec ganha uma branch própria (ex.: `feat/mvp`), que é a **Branch Alvo** do cabeçalho da spec. Push só depois que o Rafael criar o repositório no GitHub.

