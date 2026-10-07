---
trigger: model_decision
description: "Vitest, Postgres em Docker, testes HTTP, CI no GitHub Actions, deploy na Vercel e publicação só com o CI verde. Ler ao escrever testes ou mexer no CI, no compose.yml ou no deploy."
---
# Arquitetura — testes, CI e publicação

## Testes

- **Testes: Vitest 5 (decidido em 2026-09-30)**, só como `devDependency` (não vai para o deploy), com `resolve.tsconfigPaths: true` no `vitest.config.mts` para o alias `@/` funcionar sem plugin. É o caminho do guia oficial do Next 16 ("How to set up Vitest with Next.js"). O `min-release-age=1` escolhe a versão: em 2026-09-30, a 5.0.3 tinha saído no mesmo dia, então a instalada seria a 5.0.2. Na instalação, o `strict-allow-scripts` mostra se algum pacote precisa entrar no `allowScripts`.
  - Descartados:
    - **`node:test` nativo** (zero dependência). O Node 24 roda `.ts` só apagando os tipos, sem ler o `tsconfig` (doc "Modules: TypeScript"). Isso obrigaria o código de produção a importar com `.ts` no fim, trocar o alias `@/` por `#src/`, e abrir mão de `enum` e das *parameter properties* (`constructor(private readonly repo: …)`). A ferramenta de teste passaria a ditar o código de produção, e não foi verificado se o client gerado pelo Prisma roda nesse modo.
    - **Jest**, que precisa de um tradutor de TypeScript à parte (SWC ou ts-jest) e ainda tem suporte experimental a ESM.
- **Postgres dos testes e do desenvolvimento local: container Docker (decidido em 2026-09-30).** Um `compose.yml` na raiz sobe a imagem oficial `postgres` na **mesma versão major do projeto no Neon** (a definir ao criar o projeto; o Neon aceita de 14 a 18). O teste de concorrência do limite de cliques roda contra esse banco.
  - A porta fica presa ao `127.0.0.1` (`"127.0.0.1:5432:5432"`), então o banco só aceita conexões do próprio computador. A senha do `compose.yml` é só de desenvolvimento local, sem valor fora da máquina.
  - Os testes nunca conhecem a URL do Neon, e com isso não existe caminho do teste até o banco de produção.
  - O mesmo arquivo atende o "rodar localmente" do README (quem clona não precisa de conta no Neon; para o Upstash e o Google, ver `architecture-local-dev.md`) e o CI (o GitHub Actions sobe o mesmo Postgres como *service container*).
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
    - os headers da página de gestão (`Referrer-Policy`, `X-Robots-Tag`, `Cache-Control`);
    - os headers globais (RC6: `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`) numa página e nas respostas 404/410 do redirect.
  - Esses testes não precisam das chaves do Upstash nem do Google: os links são gravados direto no banco, e o redirect segue sem rate limit quando o Upstash não está disponível (fail-open). Sem as chaves, o adaptador "indisponível" responde na hora, sem esperar timeout (RC4, `security-rate-limit.md`). O `test:http` define `APP_ORIGIN=http://localhost:3000`, porque a página de gestão monta o QR com a origem canônica (RC2).
  - A tela (card, copiar, `beforeunload`) fica com um roteiro manual curto. O Playwright é evolução documentada.
  - Base: Next.js, "Guides: Testing": "we recommend using End-to-End Testing over Unit Testing for async components" (a página de gestão é um desses componentes).
  - Descartados:
    - só domínio + `curl` à mão, porque uma regressão de header ou do `HEAD` passaria com todos os testes verdes;
    - só a tradução testada sem servidor, que não pega o `export HEAD` apagado nem os headers da página de gestão, definidos na configuração do Next;
    - Playwright, que traz dependência nova com navegadores de centenas de MB e testes mais lentos, além de ser alto demais para o prazo.

## CI, deploy e publicação

- **CI no MVP (decidido em 2026-09-30): GitHub Actions completo.** A cada push, roda o lint, a checagem de tipos, o `npm test` (com o Postgres em *service container*) e o `npm run test:http`. É gratuito para repositório público (doc "GitHub Actions billing").
  - **Nenhum segredo no CI:** os testes usam serviços falsos e o Postgres do container, então o robô nunca vê as chaves do Neon, do Upstash ou do Google.
  - As ações de terceiros ficam **fixadas pelo SHA completo do commit** (`actions/checkout@<sha>`), não por tag. É o mesmo raciocínio do `save-exact`: "Pinning an action to a full-length commit SHA is currently the only way to use an action as an immutable release" (GitHub Docs, "Secure use reference").
  - O `GITHUB_TOKEN` fica com permissão mínima: `permissions: contents: read`.
  - Descartados: sem CI (um push sem rodar os testes publica o bug) e CI sem os testes HTTP (não protege os headers nem o `HEAD`, e custaria quase o mesmo).
- Onde e como faz deploy: Vercel, com deploy único (frontend e backend juntos, AD-001), via integração Git (Vercel for GitHub): push na `main` gera o deploy de produção, e as outras branches geram *previews*. O build aplica as migrations (`prisma migrate deploy`), e cada preview usa a sua branch do Neon, fechada pela Standard Protection (RC1; ver `architecture-persistence.md`, "Migrations em produção e banco dos previews").
- **Publicação só com o CI verde (decidido em 2026-09-30): duas travas, só configuração em painel, sem código.**
  - **Ruleset na `main` (GitHub):** exige que o job do CI passe antes do merge, então código só entra na `main` por Pull Request com ✓. É a garantia do "`main` sempre deployável" de `code-style.md`. Rulesets são gratuitos em repositório público (GitHub Docs, "About rulesets").
  - **Deployment Checks (Vercel), com o provider GitHub:** a Vercel faz o build da `main`, mas só o coloca no endereço público quando o job do CI passa. Se ele falhar, a versão anterior continua no ar. Cobre o que escapar do ruleset, como um push direto do administrador. "Deployment Checks are available for all projects connected to GitHub repositories" (changelog da Vercel). Existe um *Force Promote* manual para emergências.
  - O **nome do job** no YAML do CI é a referência das duas travas: renomear o job exige atualizar as regras nos dois painéis (doc "Deployment Checks", "Limitations").
  - **A confirmar no setup:** a doc diz que a Vercel segura a versão "before assigning it to your custom production domains". Verificar se o domínio `*.vercel.app` também fica retido, com um commit que falha de propósito: a versão anterior tem que continuar no ar.
  - Descartados: não bloquear (o CI só avisa depois que o bug já está no ar) e o CI publicar com `vercel deploy`, que exigiria um token da Vercel no CI e quebraria o "CI sem segredos".
