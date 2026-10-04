---
trigger: model_decision
description: "Neon (conexões pooled e direct), driver adapter @prisma/adapter-pg, pool e timeouts, variáveis da CLI do Prisma. Ler ao mexer em banco, Prisma, conexão ou migrations."
---
# Arquitetura — persistência

- Persistência: Neon (PostgreSQL serverless) via Prisma (AD-002). No Prisma 7, quem envia o SQL ao banco é um **driver adapter**, plugado no `PrismaClient` (papel equivalente ao do driver JDBC no Spring). O Neon expõe **duas conexões**:
  - **pooled** (host com `-pooler`, via PgBouncer), em `DATABASE_URL`: usada pela aplicação em runtime, porque cada função serverless abre a própria conexão e o pooler reparte poucas conexões reais entre elas;
  - **direct** (host sem `-pooler`), em `DIRECT_URL`: usada só pela CLI (`prisma migrate`), que precisa da mesma conexão do início ao fim para segurar o lock de migration. Fica configurada em `prisma.config.ts`.
  - **Variáveis da CLI do Prisma (decidido em 2026-10-02): `loadEnvConfig(process.cwd(), true)` de `@next/env` no topo do `prisma.config.ts`.** O Prisma 7 não carrega arquivos `.env` sozinho (guia "Upgrade to Prisma ORM 7", "Environment variables"). O `@next/env` é o pacote que o próprio Next usa para ler os `.env*`, e a doc do Next o indica para "a root config file for an ORM" ("Environment Variables", "Loading Environment Variables with `@next/env`").
    - Aplica a mesma precedência do `next dev`, então o `prisma migrate dev` local lê o `.env.development.local` (ver `architecture-local-dev.md`). Uma variável já definida no shell **não é sobrescrita** (`next-env/index.ts`), o que permite apontar a CLI para outro banco na linha de comando.
    - Já é dependência do `next@16.3.8` (versão `16.3.8`, sem dependências próprias), então não baixa código novo. Entra como `devDependency` explícita, na mesma versão do `next`, por causa da regra `import/no-extraneous-dependencies`.
    - Descartados: `dotenv` (dependência nova, lê o `.env` por padrão e com precedência diferente da do Next) e `process.loadEnvFile()` nativo (exigiria reescrever a precedência à mão).
  - **Driver adapter (D1, decidido em 2026-09-29): `@prisma/adapter-pg`** (TCP, lib `pg`) com **um `pg.Pool` no escopo global** de `src/data/`, registrado com **`attachDatabasePool` de `@vercel/functions`** e passado ao `PrismaPg` (o construtor da 7.10.0 aceita `pg.Pool | pg.PoolConfig | string`).
    - Motivo: com Fluid compute, a mesma instância atende vários requests, então a conexão aberta no primeiro é reaproveitada nos seguintes. O `attachDatabasePool` usa o `waitUntil` para fechar as conexões ociosas antes de a instância ser suspensa, o que evita vazamento de conexão.
    - Fontes: Neon, "Connecting to Neon from Vercel" ("With Vercel Fluid, we recommend you use a standard Postgres TCP connection […] and a connection pool") e o guia da Vercel "Connection Pooling with Vercel Functions".
    - **`idleTimeoutMillis: 5000`**, como recomenda o guia da Vercel ("a relatively short idle timeout (e.g., 5 seconds)"). O padrão do `pg` no Prisma 7 é 10 s.
    - **`connectionTimeoutMillis: 5000` (decidido em 2026-09-30).** O padrão é **0, que significa esperar para sempre** (doc de connection pool do Prisma v7). Nesse campo, o `pg` junta o tempo para abrir a conexão e o tempo para pegar uma conexão livre do pool.
      - Os 5 s cobrem com folga o *scale to zero* do Neon (acorda em "algumas centenas de milissegundos", doc "Scale to Zero") mais o handshake TCP/TLS.
      - Se o tempo estourar, o redirect responde `503` e a criação devolve erro (ver `.agents/context/redirect.md`, "Respostas do redirect").
      - Descartados: sem timeout (5 minutos de tela em branco até a Vercel matar a função, e funções presas acumulando) e 1 s (o primeiro clique depois de o Neon dormir poderia falhar à toa).
    - Descartado: `@prisma/adapter-neon` (WebSocket). Ele abre a conexão mais rápido (~4 idas e voltas contra ~8 do TCP), mas abre e fecha a cada request. O próprio Neon o recomenda só para serverless sem Fluid. Também prenderia o projeto ao Neon e complicaria o teste com Postgres local.
