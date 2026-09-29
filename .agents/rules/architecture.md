# Arquitetura — short-url

## Stack
- Linguagem/runtime: TypeScript no runtime Node.js das funções serverless da Vercel.
- **Baseline de versões (decidida em 2026-09-28):**
  - **Node 24.x** (Active LTS), fixado em `"engines": { "node": "24.x" }`. A Vercel oferece só 24.x (padrão), 22.x e 20.x, e o 20.x fica *deprecated* em 2026-10-01.
  - **Next.js 16.3.6**.
  - **Prisma 7.10.0**, com `prisma`, `@prisma/client` e o driver adapter fixados na mesma versão exata. A dist-tag `latest` do pacote `prisma` (CLI) apontava para `8.0.0-rc.17` enquanto a de `@prisma/client` apontava para `7.10.0`, então `npm i prisma` sem versão instala um RC incompatível. O Prisma 7 muda três coisas: o driver adapter é obrigatório, o generator `prisma-client` tem `output` explícito (e o client não é mais importado de `@prisma/client`), e a URL do banco vai para `prisma.config.ts`. A escolha do adapter (`@prisma/adapter-neon` ou `@prisma/adapter-pg`) fica para a spec.
  - **TypeScript 6.0.3**, não 7.x. O TS 7 (nativo, em Go) ainda não tem API JavaScript (prevista para a 7.1), e o `typescript-eslint@8.70.1`, dependência do `eslint-config-next`, declara o peer `typescript <6.1.0`. Migrar para o 7 depois é só subir uma devDependency.
  - **`.npmrc` com `save-exact=true`** e o lockfile commitado.
- **Gerenciador de pacotes: npm 11 com endurecimento de supply chain (decidido em 2026-09-28).**
  - `.npmrc` com `save-exact=true`, `min-release-age=1` (só aceita versões publicadas há mais de 1 dia, porque pacotes sequestrados costumam ser removidos em horas) e `strict-allow-scripts=true` (install falha se um pacote com script de instalação não estiver aprovado).
  - `package.json` com `"allowScripts"`, aprovando só os pacotes que precisam de script: `prisma`, `@prisma/engines`, `esbuild` e `unrs-resolver` (lista verificada em 2026-09-28; revisar a cada dependência nova).
  - As proteções atuam na máquina local, ao resolver as dependências. A Vercel instala exatamente o lockfile, então uma versão do npm na Vercel que não conheça essas opções não reabre a brecha.
  - Dependência fantasma (importar um pacote não declarado, possível no `node_modules` plano do npm): barrada por lint com a regra `import/no-extraneous-dependencies` (ver `code-style.md`).
  - Descartados: **pnpm 11**, que tem essas proteções por padrão e barra dependência fantasma por construção, mas a Vercel só documenta suporte até o pnpm 10, que lê outra configuração (`onlyBuiltDependencies` em vez de `allowBuilds`). Isso exigiria fixar a versão via Corepack e traria risco de divergência entre local e deploy. **bun**, que seria uma ferramenta a mais sem ganho, já que o runtime é Node.
- Framework principal: Next.js (App Router) + React. UI com Tailwind CSS + shadcn/ui (os componentes são copiados para o repositório, não usados como dependência caixa-preta).
- Persistência: Neon (PostgreSQL serverless) via Prisma (AD-002). No Prisma 7, quem envia o SQL ao banco é um **driver adapter**, plugado no `PrismaClient` (papel equivalente ao do driver JDBC no Spring). O Neon expõe **duas conexões**:
  - **pooled** (host com `-pooler`, via PgBouncer), em `DATABASE_URL`: usada pela aplicação em runtime, porque cada função serverless abre a própria conexão e o pooler reparte poucas conexões reais entre elas;
  - **direct** (host sem `-pooler`), em `DIRECT_URL`: usada só pela CLI (`prisma migrate`), que precisa da mesma conexão do início ao fim para segurar o lock de migration. Fica configurada em `prisma.config.ts`.
- Upstash Redis só para os contadores de rate limit (`@upstash/ratelimit`); os eventos de clique e o analytics ficam no Postgres.
- QR code: biblioteca `qrcode`, com geração local e sem API externa. É usada só na camada de entrada (ver abaixo).
- Build/bundler: o do próprio Next.js.
- Onde e como faz deploy: Vercel, com deploy único (frontend e backend juntos, AD-001). O pipeline exato (integração Git, preview por PR) será definido na spec.

## Camadas e organização de pastas

São três camadas no servidor e as dependências sempre apontam para dentro (AD-004). A estrutura abaixo é uma proposta, a confirmar na spec:

- `src/app/` — **entrada**: Pages, Route Handlers (ex.: `[slug]/route.ts` para o redirect) e Server Actions. É a única camada que importa `next/*`. O guarda de rate limit fica aqui, antes de qualquer chamada ao domínio. O redirect exporta `GET` e `HEAD`, com um `HEAD` próprio para o Next não executar o `GET` e consumir o link, e grava o evento de clique com `after()` de `next/server`. Os templates HTML do `404`, do `410` e da página neutra dos bots ficam num módulo auxiliar (ex.: `src/app/_lib/`). Ver `domain.md`, "Fluxos". A geração do QR code também fica aqui: o QR é uma apresentação do link curto que o domínio devolve, não regra de negócio, e a lib `qrcode` é dependência de terceiros que o domínio não pode importar. Fica num módulo auxiliar fora das rotas (ex.: pasta privada `src/app/_lib/`, que o App Router exclui do roteamento). O QR é gerado sob demanda a partir da URL curta e não é persistido. O formato é PNG em data URL com 512 px (ver `domain.md`, "QR code").
- `src/domain/` — **domínio**: regras de negócio em TypeScript puro (`LinkService`, `SlugGenerator`, `UrlValidator`, `ClickTracker`) e as interfaces que o domínio exige, como `LinkRepository`.
- `src/data/` — **dados**: implementações das interfaces do domínio com Prisma (ex.: `PrismaLinkRepository`) e o client Prisma singleton. É o único lugar que importa Prisma.
  - O client gerado pelo Prisma 7 fica em `src/data/generated/prisma/` (`output` do generator `prisma-client`) e é importado de lá, não de `@prisma/client`. Assim, o próprio caminho do import denuncia uma violação do AD-004: um arquivo de `src/domain/` importando `@/data/generated` é visível no review.
  - A pasta gerada não é versionada (`.gitignore`), e o build roda `prisma generate` antes do `next build`. Sem isso, o deploy falha com `Cannot find module`.
- `src/components/` — componentes React. Os do shadcn/ui ficam em `src/components/ui/`.

## Decisões não-negociáveis
- O domínio nunca importa `next/*` nem o client do Prisma. Ele recebe dependências pelo construtor (AD-004).
- Nada de SQL montado por concatenação de string. Acesso ao banco só via Prisma, com queries parametrizadas.
- O redirect usa **HTTP 302 + `Cache-Control: no-store`**, nunca 301 (o 301 é cacheado pelo navegador e perde analytics, expiração e desativação).
- A checagem de limite de cliques e de expiração é feita junto com o incremento, numa única operação atômica no banco (evita race condition).
- O slug é aleatório (CSPRNG), nunca sequencial ou enumerável.
- Sem login (AD-003). A autorização sobre um link é a posse do token de gestão.

