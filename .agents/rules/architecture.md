# Arquitetura — short-url

## Stack
- Linguagem/runtime: TypeScript no runtime Node.js das funções serverless da Vercel.
- **Baseline de versões (decidida em 2026-09-28):**
  - **Node 24.x** (Active LTS), fixado em `"engines": { "node": "24.x" }`. A Vercel oferece só 24.x (padrão), 22.x e 20.x, e o 20.x fica *deprecated* em 2026-10-01.
  - **Next.js 16.3.6**.
  - **Prisma 7.10.0**, com `prisma`, `@prisma/client` e o driver adapter fixados na mesma versão exata. A dist-tag `latest` do pacote `prisma` (CLI) apontava para `8.0.0-rc.17` enquanto a de `@prisma/client` apontava para `7.10.0`, então `npm i prisma` sem versão instala um RC incompatível. O Prisma 7 muda três coisas: o driver adapter é obrigatório, o generator `prisma-client` tem `output` explícito (e o client não é mais importado de `@prisma/client`), e a URL do banco vai para `prisma.config.ts`. O adapter escolhido é o `@prisma/adapter-pg` (ver "Persistência").
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
  - **Driver adapter (D1, decidido em 2026-09-29): `@prisma/adapter-pg`** (TCP, lib `pg`) com **um `pg.Pool` no escopo global** de `src/data/`, registrado com **`attachDatabasePool` de `@vercel/functions`** e passado ao `PrismaPg` (o construtor da 7.10.0 aceita `pg.Pool | pg.PoolConfig | string`).
    - Motivo: com Fluid compute, a mesma instância atende vários requests, então a conexão aberta no primeiro é reaproveitada nos seguintes. O `attachDatabasePool` usa o `waitUntil` para fechar as conexões ociosas antes de a instância ser suspensa, o que evita vazamento de conexão.
    - Fontes: Neon, "Connecting to Neon from Vercel" ("With Vercel Fluid, we recommend you use a standard Postgres TCP connection […] and a connection pool") e o guia da Vercel "Connection Pooling with Vercel Functions".
    - **`idleTimeoutMillis: 5000`**, como recomenda o guia da Vercel ("a relatively short idle timeout (e.g., 5 seconds)"). O padrão do `pg` no Prisma 7 é 10 s.
    - **`connectionTimeoutMillis: 5000` (decidido em 2026-09-30).** O padrão é **0, que significa esperar para sempre** (doc de connection pool do Prisma v7). Nesse campo, o `pg` junta o tempo para abrir a conexão e o tempo para pegar uma conexão livre do pool.
      - Os 5 s cobrem com folga o *scale to zero* do Neon (acorda em "algumas centenas de milissegundos", doc "Scale to Zero") mais o handshake TCP/TLS.
      - Se o tempo estourar, o redirect responde `503` e a criação devolve erro (ver `domain.md`, "Respostas do redirect").
      - Descartados: sem timeout (5 minutos de tela em branco até a Vercel matar a função, e funções presas acumulando) e 1 s (o primeiro clique depois de o Neon dormir poderia falhar à toa).
    - Descartado: `@prisma/adapter-neon` (WebSocket). Ele abre a conexão mais rápido (~4 idas e voltas contra ~8 do TCP), mas abre e fecha a cada request. O próprio Neon o recomenda só para serverless sem Fluid. Também prenderia o projeto ao Neon e complicaria o teste com Postgres local.
- Upstash Redis só para os contadores de rate limit (`@upstash/ratelimit`); os eventos de clique e o analytics ficam no Postgres.
- **Google Safe Browsing v5** (`hashes.search`) para a blocklist da R7, consultada **só na criação**, via `fetch` e `crypto.subtle` nativos, sem SDK nem dependência nova. Incluído no MVP em 2026-09-30; detalhes em `domain.md` (R7) e `security.md` ("Blocklist").
- QR code: biblioteca `qrcode`, com geração local e sem API externa. É usada só na camada de entrada (ver abaixo).
- Build/bundler: o do próprio Next.js.
- **Testes: Vitest 5 (decidido em 2026-09-30)**, só como `devDependency` (não vai para o deploy), com `resolve.tsconfigPaths: true` no `vitest.config.mts` para o alias `@/` funcionar sem plugin. É o caminho do guia oficial do Next 16 ("How to set up Vitest with Next.js"). O `min-release-age=1` escolhe a versão: em 2026-09-30, a 5.0.3 tinha saído no mesmo dia, então a instalada seria a 5.0.2. Na instalação, o `strict-allow-scripts` mostra se algum pacote precisa entrar no `allowScripts`.
  - Descartados:
    - **`node:test` nativo** (zero dependência). O Node 24 roda `.ts` só apagando os tipos, sem ler o `tsconfig` (doc "Modules: TypeScript"). Isso obrigaria o código de produção a importar com `.ts` no fim, trocar o alias `@/` por `#src/`, e abrir mão de `enum` e das *parameter properties* (`constructor(private readonly repo: …)`). A ferramenta de teste passaria a ditar o código de produção, e não foi verificado se o client gerado pelo Prisma roda nesse modo.
    - **Jest**, que precisa de um tradutor de TypeScript à parte (SWC ou ts-jest) e ainda tem suporte experimental a ESM.
- **Postgres dos testes e do desenvolvimento local: container Docker (decidido em 2026-09-30).** Um `compose.yml` na raiz sobe a imagem oficial `postgres` na **mesma versão major do projeto no Neon** (a definir ao criar o projeto; o Neon aceita de 14 a 18). O teste de concorrência do limite de cliques roda contra esse banco.
  - A porta fica presa ao `127.0.0.1` (`"127.0.0.1:5432:5432"`), então o banco só aceita conexões do próprio computador. A senha do `compose.yml` é só de desenvolvimento local, sem valor fora da máquina.
  - Os testes nunca conhecem a URL do Neon, e com isso não existe caminho do teste até o banco de produção.
  - O mesmo arquivo atende o "rodar localmente" do README (quem clona não precisa de conta no Neon; para o Upstash e o Google, ver "`npm run dev` sem chaves") e o CI (o GitHub Actions sobe o mesmo Postgres como *service container*).
  - **Os testes só gravam nesse banco local e limpam as tabelas antes de rodar** (`TRUNCATE`). A execução seguinte começa do zero, e o volume fica em kilobytes. Como vários arquivos de teste usam o mesmo banco, eles rodam **um de cada vez** (`fileParallelism: false` no Vitest), para a limpeza de um não apagar os dados de outro no meio do teste.
  - Pendente para a instalação: rodar o Docker com `sudo` ou no modo *rootless*, porque a doc do Docker avisa que "the docker group grants root-level privileges to the user".
  - Descartados:
    - **branch de teste no Neon**, porque uma `DATABASE_URL` trocada faria o teste limpar as tabelas de produção, além de depender de internet e exigir conta de quem clona;
    - **Postgres instalado via `apt`**, porque o Mint 22.3 oferece a 16, que é outra versão, e o serviço ficaria rodando sempre;
    - **PGlite**, que aceita uma conexão só: os cliques "simultâneos" rodariam em fila, e o teste de concorrência não provaria nada.
- **Testes da camada de entrada (decidido em 2026-09-30): entrada fina + testes HTTP reais.**
  - O `route.ts` e a action só repassam o trabalho. A tradução do resultado do domínio em resposta HTTP (status, headers, HTML fixo) fica em funções de `src/app/_lib/`, testadas no Vitest sem servidor.
  - Um conjunto pequeno de **testes HTTP** roda num comando separado (`npm run test:http`): sobe o site com `next build && next start` contra o Postgres do Docker, grava os links de teste direto no banco e faz requisições com `fetch` nativo, **sem dependência nova**. Conferem:
    - o status (302/404/410);
    - `Cache-Control: no-store` no redirect;
    - o `HEAD` sem incrementar `click_count`;
    - os headers da página de gestão (`Referrer-Policy`, `X-Robots-Tag`, `Cache-Control`).
  - Esses testes não precisam das chaves do Upstash nem do Google: os links são gravados direto no banco, e o redirect segue sem rate limit quando o Upstash não está disponível (fail-open).
  - A tela (card, copiar, `beforeunload`) fica com um roteiro manual curto. O Playwright é evolução documentada.
  - Base: Next.js, "Guides: Testing": "we recommend using End-to-End Testing over Unit Testing for async components" (a página de gestão é um desses componentes).
  - Descartados:
    - só domínio + `curl` à mão, porque uma regressão de header ou do `HEAD` passaria com todos os testes verdes;
    - só a tradução testada sem servidor, que não pega o `export HEAD` apagado nem os headers da página de gestão, definidos na configuração do Next;
    - Playwright, que traz dependência nova com navegadores de centenas de MB e testes mais lentos, além de ser alto demais para o prazo.
- **`npm run dev` sem chaves (decidido em 2026-10-01): serviços falsos ligados por variável explícita, com duas travas.**
  - Problema: a criação é fail-closed (ver `security.md`), então quem clona e roda `npm run dev` sem as chaves do Upstash e do Google tem toda criação recusada, e o projeto parece quebrado para quem avalia o portfólio.
  - Com `USE_LOCAL_FAKES=true`, o ponto de montagem da camada de entrada injeta dois falsos no lugar dos serviços reais:
    - `LocalFakeUrlThreatChecker` (em `src/infra/`, porque implementa o `UrlThreatChecker` do domínio): devolve `'dangerous'` só para as URLs de teste oficiais do Google (`https://testsafebrowsing.appspot.com/s/phishing.html` e `.../s/malware.html`) e `'safe'` para o resto, sem acessar a internet. Assim, o aviso da R7 (B3) pode ser visto sem conta no Google.
    - rate limiter em memória (em `src/app/_lib/`, ao lado do real, porque o rate limit é guarda da entrada), com os mesmos números de produção (10/min e 100/dia na criação, 300/min no redirect) e zerado quando o servidor reinicia.
  - **Trava 1, no ponto de montagem:** o falso só é escolhido se `NODE_ENV === 'development'` **e** `USE_LOCAL_FAKES === 'true'` (comparação estrita com a string). O Next define `development` só no `next dev` e `production` em todos os outros comandos (doc "Environment Variables"). Fora do `next dev`, a variável é ignorada e o adaptador real é usado.
  - **Trava 2, no `next.config.ts`:** o config é exportado como função que recebe a `phase` (doc "next.config.js"). Se `USE_LOCAL_FAKES === 'true'` e a fase não for `PHASE_DEVELOPMENT_SERVER` (de `next/constants`), o config lança erro com a instrução "mova o `USE_LOCAL_FAKES` para o `.env.development.local`": o `next build` e o `next start` falham. Na Vercel, o build quebra e a versão anterior continua no ar, o mesmo efeito dos Deployment Checks. O erro não fica no ponto de montagem porque estouraria em tempo de execução e poderia derrubar também o redirect, que é fail-open.
  - **Arquivo da variável (decidido em 2026-10-02): `.env.development.local`.** Quem clona roda `cp .env.example .env.development.local`. O `.env.example` vem com `USE_LOCAL_FAKES=true`, a `DATABASE_URL` do Postgres do `compose.yml` e as chaves reais em branco, com um comentário explicando as travas. Para testar os serviços reais no `npm run dev` (ex.: o adaptador do Google antes do PR), basta trocar para `false` e preencher as chaves no mesmo arquivo.
    - Motivo: o Next lê arquivos diferentes conforme o comando (`packages/next-env/index.ts`; doc "Environment Variables", "Environment Variable Load Order"). O `next dev` lê `.env.development.local` → `.env.local` → `.env.development` → `.env`; o `next build` e o `next start` leem `.env.production.local` → `.env.local` → `.env.production` → `.env`. O `.env.development.local` é o único arquivo que **só o `next dev` lê** e que **não vai para o Git** (o `.gitignore` já ignora `.env*`). No `next dev`, ele também é o de maior prioridade.
    - Descartados:
      - **`.env.local`:** o `next build` e o `npm run test:http` também o leem, então a trava 2 quebraria o build local toda vez que o Rafael fosse testar antes de um PR;
      - **`.env.development` versionado:** dispensaria o `cp`, mas criaria um `.env` commitado num repositório público, onde uma chave colada por engano seria publicada no próximo `git add .`. Também quebraria a regra "só o `.env.example` é versionado" (`security.md`).
    - Quem copiar por hábito para `.env.local` vê o `npm run dev` funcionar, e no primeiro build a trava 2 para com a instrução de correção.
  - Nada muda no CI: os testes de domínio injetam os falsos direto no construtor, e os testes HTTP gravam os links direto no banco. Nenhum dos dois lê a variável.
  - Descartados:
    - **só documentar as contas gratuitas no README:** quem clona precisaria criar conta no Upstash e um projeto no Google Cloud antes de criar o primeiro link, e cada teste manual gastaria cota real;
    - **falso automático quando falta a chave:** uma chave apagada ou digitada errada na Vercel trocaria a proteção real pelo falso **sem aviso**, e a produção passaria a aceitar URLs de golpe. Transforma uma falha visível (fail-closed) numa falha silenciosa.
- **CI no MVP (decidido em 2026-09-30): GitHub Actions completo.** A cada push, roda o lint, a checagem de tipos, o `npm test` (com o Postgres em *service container*) e o `npm run test:http`. É gratuito para repositório público (doc "GitHub Actions billing").
  - **Nenhum segredo no CI:** os testes usam serviços falsos e o Postgres do container, então o robô nunca vê as chaves do Neon, do Upstash ou do Google.
  - As ações de terceiros ficam **fixadas pelo SHA completo do commit** (`actions/checkout@<sha>`), não por tag. É o mesmo raciocínio do `save-exact`: "Pinning an action to a full-length commit SHA is currently the only way to use an action as an immutable release" (GitHub Docs, "Secure use reference").
  - O `GITHUB_TOKEN` fica com permissão mínima: `permissions: contents: read`.
  - Descartados: sem CI (um push sem rodar os testes publica o bug) e CI sem os testes HTTP (não protege os headers nem o `HEAD`, e custaria quase o mesmo).
- Onde e como faz deploy: Vercel, com deploy único (frontend e backend juntos, AD-001), via integração Git (Vercel for GitHub): push na `main` gera o deploy de produção, e as outras branches geram *previews*.
- **Publicação só com o CI verde (decidido em 2026-09-30): duas travas, só configuração em painel, sem código.**
  - **Ruleset na `main` (GitHub):** exige que o job do CI passe antes do merge, então código só entra na `main` por Pull Request com ✓. É a garantia do "`main` sempre deployável" de `code-style.md`. Rulesets são gratuitos em repositório público (GitHub Docs, "About rulesets").
  - **Deployment Checks (Vercel), com o provider GitHub:** a Vercel faz o build da `main`, mas só o coloca no endereço público quando o job do CI passa. Se ele falhar, a versão anterior continua no ar. Cobre o que escapar do ruleset, como um push direto do administrador. "Deployment Checks are available for all projects connected to GitHub repositories" (changelog da Vercel). Existe um *Force Promote* manual para emergências.
  - O **nome do job** no YAML do CI é a referência das duas travas: renomear o job exige atualizar as regras nos dois painéis (doc "Deployment Checks", "Limitations").
  - **A confirmar no setup:** a doc diz que a Vercel segura a versão "before assigning it to your custom production domains". Verificar se o domínio `*.vercel.app` também fica retido, com um commit que falha de propósito: a versão anterior tem que continuar no ar.
  - Descartados: não bloquear (o CI só avisa depois que o bug já está no ar) e o CI publicar com `vercel deploy`, que exigiria um token da Vercel no CI e quebraria o "CI sem segredos".

## Camadas e organização de pastas

São três camadas no servidor (entrada, domínio e adaptadores), e as dependências sempre apontam para dentro (AD-004). A camada de adaptadores fica em **duas pastas**, `src/data/` (banco) e `src/infra/` (serviços externos), decididas na B2 em 2026-09-30. A estrutura abaixo é uma proposta, a confirmar na spec:

```
src/
├── app/          → entrada: páginas, Route Handlers, Server Actions (única camada com next/*)
│   └── _lib/     → auxiliares fora do roteamento: templates HTML, QR code, rate limit
├── domain/       → regras de negócio em TypeScript puro + interfaces (portas)
├── data/         → adaptador do banco: Prisma (único lugar que importa Prisma)
│   └── generated/prisma/   → client gerado (não versionado)
├── infra/        → adaptadores de serviços externos (ex.: Google Safe Browsing)
└── components/   → componentes React (shadcn/ui em components/ui/)
```

Direção das dependências: `app` → `domain` ← `data` e `infra`. O domínio não importa nenhuma das outras pastas; `data` e `infra` implementam as interfaces dele, e a entrada monta tudo, injetando os adaptadores pelo construtor.

- `src/app/` — **entrada**: Pages, Route Handlers (ex.: `[slug]/route.ts` para o redirect) e Server Actions. É a única camada que importa `next/*`. O guarda de rate limit fica aqui, antes de qualquer chamada ao domínio. O redirect exporta `GET` e `HEAD`, com um `HEAD` próprio para o Next não executar o `GET` e consumir o link, e grava o evento de clique com `after()` de `next/server`. Os templates HTML do `404`, do `410` e da página neutra dos bots ficam num módulo auxiliar (ex.: `src/app/_lib/`). Ver `domain.md`, "Fluxos". A geração do QR code também fica aqui: o QR é uma apresentação do link curto que o domínio devolve, não regra de negócio, e a lib `qrcode` é dependência de terceiros que o domínio não pode importar. Fica num módulo auxiliar fora das rotas (ex.: pasta privada `src/app/_lib/`, que o App Router exclui do roteamento). O QR é gerado sob demanda a partir da URL curta e não é persistido. Duas telas usam a mesma função: o card de criação e a página de gestão (P1b). O formato é PNG em data URL com 512 px (ver `domain.md`, "QR code").
- `src/domain/` — **domínio**: regras de negócio em TypeScript puro (`LinkService`, `SlugGenerator`, `UrlValidator`, `ClickTracker`) e as interfaces que o domínio exige, como `LinkRepository` e `UrlThreatChecker` (R7).
- `src/data/` — **dados**: implementações das interfaces do domínio com Prisma (ex.: `PrismaLinkRepository`) e o client Prisma singleton. É o único lugar que importa Prisma.
  - O client gerado pelo Prisma 7 fica em `src/data/generated/prisma/` (`output` do generator `prisma-client`) e é importado de lá, não de `@prisma/client`. Assim, o próprio caminho do import denuncia uma violação do AD-004: um arquivo de `src/domain/` importando `@/data/generated` é visível no review.
  - A pasta gerada não é versionada (`.gitignore`), e o build roda `prisma generate` antes do `next build`. Sem isso, o deploy falha com `Cannot find module`.
- `src/infra/` — **integrações externas** (B2, decidida em 2026-09-30): adaptadores que implementam interfaces do domínio falando com serviços de fora que não são o banco. Hoje: `SafeBrowsingUrlThreatChecker` (arquivo `safe-browsing-url-threat-checker.ts`), que implementa o `UrlThreatChecker` da R7 com `fetch` e `crypto.subtle` nativos, e o `LocalFakeUrlThreatChecker`, usado só no `npm run dev` (ver "`npm run dev` sem chaves"). É o lugar das evoluções documentadas (Google Web Risk no lugar do Safe Browsing, fila com retry para os eventos de clique).
  - Motivo da pasta separada: `src/data/` continua com um papel só ("o único lugar que importa Prisma"), e o nome de cada pasta diz o que tem dentro. Descartado: pôr o adaptador em `src/data/`, que viraria "banco e serviços externos".
  - O rate limit (Upstash) **não** vai para cá: é um guarda da camada de entrada (AD-004), não uma interface do domínio.
- `src/components/` — componentes React. Os do shadcn/ui ficam em `src/components/ui/`.

## Decisões não-negociáveis
- O domínio nunca importa `next/*`, o client do Prisma nem nada de `src/data/` ou `src/infra/`. Ele recebe as dependências pelo construtor (AD-004).
- Nada de SQL montado por concatenação de string. Acesso ao banco só via Prisma, com queries parametrizadas.
- O redirect usa **HTTP 302 + `Cache-Control: no-store`**, nunca 301 (o 301 é cacheado pelo navegador e perde analytics, expiração e desativação).
- A checagem de desativação, de limite de cliques e de expiração é feita junto com o incremento, numa única operação atômica no banco (evita race condition).
- O slug é aleatório (CSPRNG), nunca sequencial ou enumerável.
- Sem login (AD-003). A autorização sobre um link é a posse do token de gestão.

