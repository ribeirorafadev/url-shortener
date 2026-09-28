# short-url — Log de Decisões Arquiteturais (ADR)

Log append-only. Nunca editar ou apagar entrada antiga — para substituir, crie nova `AD-NNN` e marque a antiga como `superseded by AD-NNN`.

Critério pra virar entrada aqui (os três, simultâneos): difícil de reverter, surpreendente sem contexto, produto de trade-off real. Ver `.agents/rules/spec-workflow.md`.

## Template de entrada

```markdown
## AD-NNN: <título curto da decisão>

**Data:** YYYY-MM-DD
**Origem:** `specs/[data]-[slug]-design.md` (ou "N/A" se a decisão não veio de uma spec)
**Contexto:** <1-3 frases: qual problema ou trade-off forçou a decisão>
**Decisão:** <o que foi decidido>
**Alternativas consideradas:** <opcional — só quando a rejeição de uma alternativa não é óbvia>
```

`**Origem:**` é o que fecha o ciclo spec → decisão: aponta pro arquivo de spec que gerou a decisão, não só descreve a decisão isolada.

---

## AD-001: Next.js full-stack unificado na Vercel, sem backend separado

**Data:** 2026-09-24
**Origem:** N/A — sessão de brainstorming de 2026-09-23/24, anterior à primeira spec
**Contexto:** O projeto precisa ser full-stack, em Node.js/TypeScript, e ficar pronto em 1 semana. No free tier do Render, que o autor já usou, o serviço hiberna após ~15 min sem acesso, e a primeira requisição depois disso leva de 30 a 50+ segundos. Para um link de portfólio aberto por um recrutador, isso parece aplicação quebrada.
**Decisão:** Um único app Next.js (App Router), com frontend e backend no mesmo projeto e deploy único na Vercel. O backend são Route Handlers e Server Actions em TypeScript, executados como funções serverless em runtime Node.js. Não existe processo de servidor sempre ligado, então o problema de hibernação não se aplica.
**Alternativas consideradas:** API separada em Express/Fastify no Render + SPA React/Vite na Vercel. Ela deixaria mais nítida a narrativa de "API standalone", mas sofre a hibernação do Render, dobra a infraestrutura (dois deploys, CORS) e aumenta o risco de estourar o prazo. Se um repositório de API standalone fizer falta no portfólio, ele vira um projeto separado.

## AD-002: Prisma como ORM, sobre Neon (PostgreSQL serverless)

**Data:** 2026-09-24
**Origem:** N/A — sessão de brainstorming de 2026-09-23/24, anterior à primeira spec
**Contexto:** Funções serverless abrem conexões com o banco a cada invocação, e um Postgres tradicional sem pooling esgota as conexões. É o primeiro contato do autor com ORM, e o prazo é de 1 semana. A política de segurança proíbe SQL montado por concatenação.
**Decisão:** Prisma é o único meio de acesso ao banco. O banco é o Neon, que tem connection pooling nativo e resolve a tensão entre Prisma e serverless. A escolha do Neon é fácil de reverter (é Postgres padrão, basta trocar a connection string). O custo de reversão está no Prisma, porque ele molda toda a camada de dados.
**Alternativas consideradas:** O Drizzle é mais leve, tem cold start menor em serverless e fica mais próximo de SQL. Foi rejeitado pela curva de aprendizado maior para quem nunca usou ORM e pelo prazo; fica como opção para projetos futuros. O Supabase foi rejeitado porque vem empacotado com auth, storage e realtime, que o projeto não usa (ver AD-003).

## AD-003: Sem contas de usuário; cada link é gerenciado por um token secreto

**Data:** 2026-09-24
**Origem:** N/A — sessão de brainstorming de 2026-09-23/24, anterior à primeira spec
**Contexto:** A motivação para ter login seria segurança contra DDoS e abuso. Mas login não mitiga DDoS, que é um ataque de infraestrutura e já é absorvido pela edge da Vercel. Também não é necessário contra abuso funcional, que o rate limiting cobre com ou sem login. E login adiciona superfície de ataque (senhas, sessão, recuperação de conta), além de competir em tema com o Projeto B do portfólio (IAM), onde autenticação é o foco.
**Decisão:** A ferramenta é pública e sem login. Ao criar um link, o sistema gera um slug público curto e um token de gestão longo e aleatório, exibido uma única vez. A URL `/manage/[token]` dá acesso às estatísticas e à desativação daquele link: quem tem o token tem autorização sobre o link. É o padrão usado por Pastebin e PrivateBin.
**Alternativas consideradas:** Contas de usuário (ex.: NextAuth), com dashboard privado por usuário. Rejeitada pelos motivos do contexto: seria segurança de fachada nesse modelo de ameaça.

## AD-004: Arquitetura em camadas com domínio em TypeScript puro

**Data:** 2026-09-24
**Origem:** N/A — sessão de brainstorming de 2026-09-23/24, anterior à primeira spec
**Contexto:** O Next.js junta UI e backend no mesmo projeto. Sem uma fronteira explícita, a regra de negócio se espalha por route handlers e componentes, fica difícil de testar sem banco e servidor, e o projeto perde valor como prova de backend no portfólio.
**Decisão:** O código do servidor fica em três camadas:
- **Entrada** (Pages, Route Handlers, Server Actions): única camada que importa `next/*`. Inclui o guarda de rate limit, que é uma preocupação transversal (como um `Filter` no Spring), não regra de negócio.
- **Domínio**: TypeScript puro (`LinkService`, `SlugGenerator`, `UrlValidator`, `ClickTracker`, `QrCodeGenerator`). Não importa Next.js nem Prisma. Define as interfaces de que precisa, como `LinkRepository`.
- **Dados**: implementa essas interfaces com Prisma. É o único lugar que importa o client do Prisma.

As dependências sempre apontam para dentro: é a Dependency Rule de Robert C. Martin (*Clean Architecture*, cap. 22) e o "D" do SOLID.
**Alternativas consideradas:** Regra de negócio direto nos route handlers e server actions. Teria menos arquivos, mas acopla a regra ao framework e exige banco para testar qualquer regra.
