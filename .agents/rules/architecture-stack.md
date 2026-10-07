---
trigger: model_decision
description: "Linguagem, baseline de versões (Node, Next, Prisma, TypeScript), npm endurecido contra supply chain, framework e serviços/bibliotecas externos (Upstash, Safe Browsing, qrcode). Ler ao instalar ou atualizar dependências e ao escolher biblioteca."
---
# Arquitetura — stack e versões

- Linguagem/runtime: TypeScript no runtime Node.js das funções serverless da Vercel.
- **Baseline de versões (decidida em 2026-09-28):**
  - **Node 24.x** (Active LTS), fixado em `"engines": { "node": "24.x" }`. A Vercel oferece só 24.x (padrão), 22.x e 20.x, e o 20.x fica *deprecated* em 2026-10-01.
  - **Next.js 16.3.8** (subiu da 16.3.6 em 2026-10-02), com o `eslint-config-next` na mesma versão. A 16.3.8 (30/09) traz correções de segurança: uma High (SSRF no Image Optimization, GHSA-cjq9-62q9-8jv4) e cinco Medium (cache poisoning em SSG/ISR e vazamentos do `use cache`). A 16.3.7 só corrigia um travamento do Turbopack. Fonte: release notes `vercel/next.js` v16.3.7 e v16.3.8.
  - **Prisma 7.10.0**, com `prisma`, `@prisma/client` e o driver adapter fixados na mesma versão exata. A dist-tag `latest` do pacote `prisma` (CLI) apontava para `8.0.0-rc.17` enquanto a de `@prisma/client` apontava para `7.10.0`, então `npm i prisma` sem versão instala um RC incompatível. O Prisma 7 muda três coisas: o driver adapter é obrigatório, o generator `prisma-client` tem `output` explícito (e o client não é mais importado de `@prisma/client`), e a URL do banco vai para `prisma.config.ts`. O adapter escolhido é o `@prisma/adapter-pg` (ver `architecture-persistence.md`).
  - **TypeScript 6.0.3**, não 7.x. O TS 7 (nativo, em Go) ainda não tem API JavaScript (prevista para a 7.1), e o `typescript-eslint` (8.70.1 em 2026-09-28; 8.71.0 em 2026-10-02), dependência do `eslint-config-next`, declara o peer `typescript <6.1.0`. Migrar para o 7 depois é só subir uma devDependency.
  - **`.npmrc` com `save-exact=true`** e o lockfile commitado.
- **Gerenciador de pacotes: npm 11 com endurecimento de supply chain (decidido em 2026-09-28).**
  - `.npmrc` com `save-exact=true`, `min-release-age=1` (só aceita versões publicadas há mais de 1 dia, porque pacotes sequestrados costumam ser removidos em horas) e `strict-allow-scripts=true` (install falha se um pacote com script de instalação não estiver aprovado).
  - `package.json` com `"allowScripts"`, aprovando só os pacotes que precisam de script: `prisma`, `@prisma/engines`, `esbuild` e `unrs-resolver` (lista verificada em 2026-09-28; revisar a cada dependência nova). O `qrcode@1.5.4` e as dependências dele não têm script de instalação (verificado em 2026-10-02).
  - As proteções atuam na máquina local, ao resolver as dependências. A Vercel instala exatamente o lockfile, então uma versão do npm na Vercel que não conheça essas opções não reabre a brecha.
  - Dependência fantasma (importar um pacote não declarado, possível no `node_modules` plano do npm): barrada por lint com a regra `import/no-extraneous-dependencies` (ver `code-style.md`).
  - Descartados: **pnpm 11**, que tem essas proteções por padrão e barra dependência fantasma por construção, mas a Vercel só documenta suporte até o pnpm 10, que lê outra configuração (`onlyBuiltDependencies` em vez de `allowBuilds`). Isso exigiria fixar a versão via Corepack e traria risco de divergência entre local e deploy. **bun**, que seria uma ferramenta a mais sem ganho, já que o runtime é Node.
- Framework principal: Next.js (App Router) + React. UI com Tailwind CSS + shadcn/ui (os componentes são copiados para o repositório, não usados como dependência caixa-preta).
- Upstash Redis só para os contadores de rate limit (`@upstash/ratelimit`); os eventos de clique e o analytics ficam no Postgres.
- `@vercel/functions`: `attachDatabasePool` (pool do Postgres, `architecture-persistence.md`) e `ipAddress` (IP do rate limit, `security-rate-limit.md`).
- Neon ↔ Vercel pela **Neon-Managed Integration**, que cria uma branch do banco por preview (RC1, `architecture-persistence.md`).
- **Google Safe Browsing v5** (`hashes.search`) para a blocklist da R7, consultada **só na criação**, via `fetch` e `crypto.subtle` nativos, sem SDK nem dependência nova. Incluído no MVP em 2026-09-30; detalhes em `.agents/context/url-validation.md` (R7) e `security-blocklist.md`.
- QR code: biblioteca **`qrcode@1.5.4`**, com geração local e sem API externa. É usada só na camada de entrada (ver `architecture-layers.md`).
  - **Dependências transitivas avaliadas (decidido em 2026-10-02): manter.** Instalação isolada: 29 pacotes, 2,6 MB, `npm audit` com 0 vulnerabilidades e nenhum script de instalação. O código da biblioteca (`lib/`) só importa `pngjs`, `dijkstrajs` e `fs`; o `yargs@15` é usado só pela CLI dela (`bin/`), nunca em tempo de execução.
  - Descartado: `qrcode-generator` (sem dependências) com um codificador PNG próprio sobre `node:zlib` (`deflateSync` e `crc32`, nativos no Node 24), que acrescentaria código nosso para testar sem ganho real de segurança. O `qrcode-generator` sozinho gera GIF, e o WhatsApp trata GIF como animação.
- Build/bundler: o do próprio Next.js.
