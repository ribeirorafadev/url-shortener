# short-url — Handoff

**Atualizado em:** 2026-09-30
**Sessões anteriores:**
- 2026-09-23/24: brainstorming inicial (stack, arquitetura, AD-001 a AD-004).
- 2026-09-24 a 27: ajuste do system design, modelo de dados e decisões de segurança e produto.
- 2026-09-28: baseline de versões, Prisma 7, `SERIAL` nas PKs, npm endurecido, kebab-case, pt-BR, padrão de commit, contrato completo da `createLink` (6a a 6c), Excalidraw atualizado, `git init` e push para o GitHub (seção 2b).
- 2026-09-29/30 (última sessão):
  - **7a a 7e:** redirect `GET`/`HEAD /[slug]`;
  - **8a e 8b:** página de gestão;
  - **9a e 9b:** `deactivateLink`;
  - **D1:** driver adapter;
  - **10a a 10e:** tratamento de erros (rate limiter fora do ar, números, IPv6, colisão de slug, timeout do banco);
  - **mapa de erros** aprovado;
  - correção de um defeito no SQL atômico (seções 2c e 2d);
  - **P1 a P6** decididos;
  - **blocklist (Google Safe Browsing, regra R7) incluída no MVP** (seção 2e).

**Fase atual:** design, seguindo `superpowers:brainstorming` pelo **caminho arquitetural**. **Nenhum código foi escrito, e isso é intencional.** O hard-gate da skill só libera a implementação depois de três passos: spec escrita e aprovada, plano (`superpowers:writing-plans`) aprovado e método de execução escolhido.
**Próxima etapa:** as **3 decisões da blocklist (B1 a B3, seção 2e)**, uma por mensagem, começando pela **B1** (Safe Browsing fora do ar). Depois, o **P7** (último da pauta, seção 2d). Depois, a estratégia de testes.

### Como retomar (primeiros passos da nova sessão)
1. `git status -sb` deve mostrar `main...origin/main` sem pendências. Se houver algo, pergunte ao Rafael antes de mexer.
2. Invoque `superpowers:brainstorming`: a sessão continua no **caminho arquitetural**, na etapa "apresentar o design em seções". Nada de código antes da spec e do plano aprovados.
3. Apresente a **B1** no formato de "What Worked": cenário concreto, cada opção em 1–2 frases com uma mini linha do tempo, tabela curta sem jargão, recomendação. Registre no arquivo certo assim que o Rafael fechar, e siga para B2, B3 e P7.
4. Depois do P7, siga a ordem dos Next Steps: estratégia de testes → spec.
5. **Commite e dê push ao fim de cada bloco de decisões** (com autorização do Rafael). Em 2026-09-30, um Ctrl+Z no editor desfez edições ainda não commitadas (ver "What Didn't Work").

---

## Goal

Construir um **encurtador de links com analytics** como primeiro projeto do portfólio full-stack do Rafael, em cerca de 1 semana. O papel do projeto é diversificar a stack (Node.js/TypeScript) antes dos projetos B (IAM) e A (CRM), que serão em Java/Spring. O roadmap está em `~/Projetos/portfolio-roadmap.txt`.

O escopo do MVP, o que ficou fora de escopo e o critério de "pronto" estão em `docs/superpowers/PRD.md`.

## Onde está cada coisa (fontes da verdade)

| Arquivo | Conteúdo |
|---|---|
| `docs/superpowers/PRD.md` | Problema, público, escopo do MVP (inclui **idioma pt-BR**, **blocklist R7** e **QR na página de gestão**), **fora de escopo** (inclui alias, edição de destino, i18n e reverificação periódica, com os motivos) e critério de "pronto" |
| `docs/superpowers/ADR.md` | AD-001 a AD-004. É append-only: **nunca editar** |
| `.agents/rules/architecture.md` | Stack, **baseline de versões**, **npm endurecido** (e por que não pnpm/bun), conexões pooled/direct do Neon, **driver adapter `@prisma/adapter-pg` com `attachDatabasePool` e os timeouts do pool (D1, 10e)**, camadas, pastas (client Prisma gerado em `src/data/generated/prisma/`) e decisões não negociáveis. O QR code fica na camada de entrada |
| `.agents/rules/code-style.md` | Lint (restrição do TS 6, `import/no-extraneous-dependencies`, candidata `no-restricted-imports`), **arquivos em kebab-case**, **padrão de commit** e branches |
| `.agents/rules/security.md` | Ameaças (phishing com R1 a R7), política (segredos, **`.npmrc` sem token**, artefatos de teste ignorados), ameaças novas de 2026-09-29 (HEAD/bots, varredura de caminhos, **CSRF das Server Actions**), **decidido** (hash e formato do token, IP não persistido), **vazamentos do token** (Referer mitigado, logs e histórico aceitos), **números do rate limit e chave `/64` no IPv6 (10b, 10c)**, **rate limiter indisponível: fail-open no redirect, fail-closed na criação (10a)** e **blocklist do Safe Browsing: privacidade, custo, cota e API key** |
| `.agents/context/domain.md` | Glossário, regras de negócio (**validação R1 a R7**, **`trim()` (P4)**, **IDN/homógrafo (P6)**, **limite e expiração**, **colisão de slug**, **pré-validação do slug**, **respostas 302/404/410/429/503 e páginas do redirect**, **SQL atômico corrigido**, **registro com `after()`**, **token e contrato da `createLink`** (QR opcional, P1; duplo envio, P3; perda do token, P5), **parâmetros ignorados (P2)**, QR), **bots de preview e `HEAD`**, fluxos (criação e redirect passo a passo), **modelo de dados completo**, **página de gestão** (janela, desativação irreversível e idempotente) e **mapa de erros** |
| `.gitignore` | Por seções; ignora `.env*` (exceto `.env.example`), chaves e certificados, o client gerado do Prisma e os artefatos de teste (`.playwright-mcp/`, `test-results/`) |
| Excalidraw (navegador do Rafael) | Documentação visual (ver seção 3) |

## Current Progress

### 1. Decisões fechadas antes desta sessão (não reabrir sem motivo novo)
- **Stack:** Next.js (App Router) full-stack na Vercel (AD-001), Prisma + Neon (AD-002), Upstash **só** para rate limit, Tailwind + shadcn/ui e lib `qrcode`.
- **Sem login:** a gestão é feita por um token secreto (AD-003).
- **Três camadas:** entrada `src/app`, domínio `src/domain` (TS puro) e dados `src/data` (único lugar com Prisma). Ver AD-004.
- **Redirect:** 302 + `no-store`, 404 ou 410. Slug base62 de 7 caracteres via CSPRNG. Incremento atômico. Registro do clique fora do caminho crítico. Rate limiter como guarda na camada de entrada.

### 2. Decidido na sessão de 2026-09-24 a 27

**System design e arquitetura**
- **QR code saiu do domínio e foi para a camada de entrada.** É apresentação do link, e a lib `qrcode` é de terceiros. Ele é gerado sob demanda e não é persistido; a sugestão de local é `src/app/_lib/`.
  - Já está atualizado em `architecture.md` e `domain.md`.
  - ⚠️ O **AD-004 ainda cita `QrCodeGenerator`** no domínio e não pode ser editado, porque o log é append-only. A mudança não passa no critério de ADR (é fácil de reverter). **A spec deve registrar isso explicitamente.**
- **Identificadores de código em inglês:** `createLink`, `deactivateLink`, no mesmo idioma de `LinkService` etc.

**Decisões de produto, segurança e modelo de dados.** Cada uma foi debatida com trade-offs, a pedido do Rafael.

| # | Decisão | Escolha | Registrada em |
|---|---|---|---|
| 1 | Token de gestão no banco | **Só o hash SHA-256**: `BYTEA(32)` com `UNIQUE`, via Web Crypto. O token tem 256 bits, então um hash rápido basta | `security.md` |
| 2 | IP do visitante | **Não persistir**: LGPD art. 6º, III, e evita que a ferramenta vire "IP logger". Marco Civil art. 15 não se aplica a pessoa física | `security.md` |
| 3 | Alias personalizado | **Fora do MVP**: amplifica phishing por squatting e colide com rotas. Evolução documentada | `PRD.md` |
| 4 | Editar a URL de destino | **Imutável**. Evolução: editável só até o 1º clique (`WHERE click_count = 0`) | `PRD.md` |
| 5 | Chave primária | `links.id Int` (`SERIAL`) e `click_events.id BigInt` (`BIGSERIAL`), corrigido em 2026-09-28 (seção 2b). São internas; as públicas são o slug e o token | `domain.md` |
| 6 | Dispositivo | **Só a categoria** (enum), classificada no clique por função pura: `Sec-CH-UA-Mobile`, depois regex no UA. `TABLET` é mantido, e o iPad aparece como DESKTOP (limitação documentada) | `domain.md` |
| 7 | Referrer | **Só o host normalizado** (`new URL()`, http/https, minúsculas, sem `www.`); `null` significa direto | `domain.md` |
| 8 | Fuso do "dia" nas estatísticas | `America/Sao_Paulo` fixo, com o rótulo "horário de Brasília". Evolução: fuso do navegador | `domain.md` |
| 9 | Bots de preview | Link **sem limite**: 302 para todos, e bot não conta. Link **com limite**: bot recebe um `200` numa página neutra, sem destino e sem consumir, o que anula o bypass por UA forjado. Registro como `device_type = BOT`, fora dos totais. Lista própria de UAs no domínio. Evolução: página de confirmação (POST) para links com limite | `domain.md` |

**Schema resultante** (detalhes em `domain.md`, seção "Modelo de dados"):
- **`links`:**
  - `id` int (`SERIAL`) PK;
  - `slug` text UK;
  - `destination_url` text;
  - `manage_token_hash` bytea UK;
  - `click_count` int, default 0;
  - `max_clicks` int null;
  - `expires_at`, `deactivated_at` e `created_at`, todos `timestamptz(3)`.
- **`click_events`:**
  - `id` bigint (`BIGSERIAL`) PK;
  - `link_id` int FK com `RESTRICT`;
  - `clicked_at` timestamptz;
  - `device_type` enum (`MOBILE`, `DESKTOP`, `TABLET`, `BOT`, `UNKNOWN`);
  - `referrer_host` text null;
  - índice `(link_id, clicked_at)`.
- **Redirect:** `updateManyAndReturn` (Prisma ≥ 6.2.0) faz o UPDATE atômico com RETURNING. Se vier vazio, um `findUnique({ slug })` decide entre 404 e 410.

**Pendências e limitações documentadas** (não esquecer na spec):
- ✅ **Vazamentos do token que o hash não cobre:** tratados na decisão 8b (seção 2c). O Referer foi mitigado; os logs da Vercel e o histórico ficaram como risco aceito, documentado em `security.md`, "Vazamentos do token".
- **Scanners de e-mail** (Defender Safe Links, Proofpoint, Mimecast) consomem links com limite, porque usam UA de navegador comum. A raiz está na RFC 9110, §9.2.1 (GET seguro). A página de confirmação fica como evolução.
- `click_count` e os totais de `click_events` podem divergir um pouco, porque o evento é gravado depois da resposta.

### 2b. Decidido em 2026-09-28

**Baseline de versões** (registrada em `architecture.md`, "Stack"). Tudo verificado no npm registry, em `nodejs.org/dist/index.json` e nas documentações da Vercel, do Next.js e do Prisma:

| Item | Versão | Motivo |
|---|---|---|
| Node | **24.x** (Active LTS), `"engines": { "node": "24.x" }` | A Vercel só oferece 24/22/20, e o 20 fica *deprecated* em 2026-10-01 |
| Next.js | **16.3.6** | É a `latest`; exige Node ≥ 20.9 |
| Prisma | **7.10.0** exato em `prisma`, `@prisma/client` e no adapter | ⚠️ A dist-tag `latest` do CLI `prisma` aponta para `8.0.0-rc.17`. Instalar sempre com a versão explícita |
| TypeScript | **6.0.3** | O TS 7 não tem API JS, e o `typescript-eslint@8.70.1` (via `eslint-config-next`) exige TS `<6.1.0`. Com o TS 7, o `npm run lint` quebra em todo `.ts` |
| npm | `.npmrc` com `save-exact=true` e o lockfile commitado | Pinning: versão exata, sem `^` |

**Impacto do Prisma 7 no design** (registrado em `architecture.md`):
- O **driver adapter** é obrigatório: o Prisma gera o SQL e o adapter o envia (análogo ao JDBC).
- O Neon tem duas conexões: **pooled** (`DATABASE_URL`, host `-pooler`, para a app) e **direct** (`DIRECT_URL`, para `prisma migrate`, que precisa de conexão fixa por causa do lock).
- O client é gerado em `src/data/generated/prisma/` (no `.gitignore`), e o build roda `prisma generate && next build`.
- `DIRECT_URL` entrou na lista de segredos de `security.md`.
- O `updateManyAndReturn` foi confirmado na referência v7. O Prisma 8 (RC) o renomeia para `updateAll()` (nota em `domain.md`).
- **Nenhuma regra de negócio mudou**, e o schema também não, exceto o item abaixo.

**PKs `SERIAL`/`BIGSERIAL` em vez de `IDENTITY`** (registrado em `domain.md`). O Prisma gera `SERIAL` com `autoincrement()`, e a documentação dizia `identity`. O Rafael aceitou o `SERIAL`: só o repositório insere, sempre sem id, e manter o `IDENTITY` exigiria editar toda migration à mão.

**Demais decisões de 2026-09-28** (uma por mensagem, com trade-offs):

| # | Decisão | Escolha | Registrada em |
|---|---|---|---|
| 2 | Gerenciador de pacotes | **npm 11 endurecido:** `.npmrc` com `save-exact`, `min-release-age=1` e `strict-allow-scripts=true`; `allowScripts` (prisma, @prisma/engines, esbuild, unrs-resolver); dependência fantasma barrada por `import/no-extraneous-dependencies`. O pnpm 11 foi descartado porque a Vercel só documenta até o pnpm 10 | `architecture.md`, `code-style.md` |
| 3 | Nome de arquivo | **kebab-case em tudo** (padrão do shadcn e do Next; elimina bugs de caixa entre Mac/Windows e o Linux da Vercel) | `code-style.md` |
| 4 | Idioma | **pt-BR** na UI e no README (alvo: vagas no Brasil). i18n fora de escopo: `[lang]` colide com `[slug]` na raiz | `PRD.md` |
| 5 | Commits | **Conventional Commits**, tipo e escopo em inglês, descrição em pt-BR, sem validação automática, **trailer do Claude mantido**; `main` "deployável" e uma branch por spec | `code-style.md` |
| 6a | URL de destino | **R1** http/https (com **aviso** para `http:`), **R2** sem credenciais na URL, **R3** não pode ser o próprio domínio, **R4** host público, **R5** no máximo 2048 caracteres, **R6** prefixa `https://` quando falta protocolo | `domain.md`, `security.md` |
| 6b | Limite e expiração | Limite de 1 a 1.000.000 (conversão estrita); expiração por duração (1 h, 24 h, 7 dias, 30 dias) ou fim do dia em `America/Sao_Paulo` via `Intl` (sem `Temporal` no Node 24), com máximo de 5 anos | `domain.md` |
| 6c | Resposta da `createLink` | Token base64url (43 caracteres); estado discriminado `CreateLinkState`; exibição única num card na tela de criação; QR em PNG de 512 px | `domain.md`, `security.md` |

**Outros arquivos atualizados:** `CLAUDE.md` (stack com versões) e `.gitignore` (reorganizado; ver "Repositório"). O ADR não mudou, porque nenhuma dessas decisões passa nos três critérios. O PRD mudou só com o idioma e o i18n.

### 2c. Decidido em 2026-09-29

**Premissas verificadas** (context7, docs da Vercel e código-fonte do Next):
- `after()` de `next/server` funciona em Route Handler. Na Vercel, usa o `waitUntil` da plataforma e vive até o `maxDuration` da rota (**300 s no Hobby** com Fluid compute, ligado por padrão). Erro no callback vira `console.error` do Next, **sem retry**.
- **Next 16 responde `HEAD` executando o `GET`** quando a rota não exporta `HEAD` (`auto-implement-methods.ts`).
- **CSRF das Server Actions:** o Next compara `Origin` com `Host`/`X-Forwarded-Host`; sem `allowedOrigins`, só a mesma origem passa.
- **Logs de runtime da Vercel** mostram o path acessado, e o **Hobby guarda 1 hora**.

| # | Decisão | Escolha | Registrada em |
|---|---|---|---|
| 7a | Quando gravar o evento de clique | **Depois de responder, com `after()`**. Headers classificados antes (`ClickTracker`), e o callback só grava. Uma falha não afeta o visitante (divergência já aceita). Descartados: gravar antes do 302 e CTE UPDATE+INSERT | `domain.md` |
| 7b | Requisições `HEAD` | **`HEAD` próprio, tratado como bot de preview**: só lê, não incrementa, não gera evento; link com limite recebe `200` sem destino. RFC 9110, §9.1 e §9.2.1. Descartados: padrão do Next (gasta o link) e `405` | `domain.md` |
| 7c | Corpo do 404/410/página neutra | **HTML mínimo em pt-BR gerado no Route Handler**, texto fixo (sem XSS), `no-store`. Descartados: texto puro e redirect para página React (perderia o `410` exigido pelo PRD) | `domain.md` |
| 7d | O 410 mostra o motivo? | **Sim, três textos fixos** (desativado / expirou / limite), com precedência desativado → expirado → esgotado. Sem data nem número | `domain.md` |
| 7e | Formato do slug | **`isValidSlugFormat` (domínio, `^[A-Za-z0-9]{7}$`) antes do rate limit e do banco** → `404` imediato para `/wp-login.php` etc. | `domain.md` |
| 8a | Janela do gráfico diário | **Últimos 30 dias** (ou desde a criação, se for mais novo). Totais cobrem toda a vida do link. Seletor 7/30/90 é evolução | `domain.md` |
| 8b | Token na URL de gestão | **Continua no path** + `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex` e `no-store`. Logs da Vercel viram **exceção documentada** (só o dono vê, 1 h); histórico é risco residual. Descartados: fragmento `#` (dashboard no cliente) e campo "cole o token" | `security.md`, `domain.md` |

**Outros arquivos atualizados:**
- `domain.md`: fluxo do redirect detalhado passo a passo e nova seção "Página de gestão";
- `security.md`: 3 ameaças novas e a seção "Pendente de mitigação" substituída por "Vazamentos do token";
- `architecture.md`: `GET`/`HEAD`, `after()` e templates HTML na camada de entrada;
- `PRD.md`: referência aos vazamentos do token.

O ADR não mudou. O 8b é o caso mais próximo, porque mudar o formato da URL de gestão depois quebraria links já entregues, mas fica na spec: dá para migrar aceitando os dois formatos.

### 2d. Decidido em 2026-09-29/30 (segunda parte)

**Premissas verificadas:**
- **Neon**, "Connecting to Neon from Vercel": com Fluid compute, recomenda TCP (`pg`) com pool. O driver serverless fica para serverless sem Fluid. Na abertura de conexão, o TCP leva ~8 idas e voltas e o WebSocket ~4.
- **Vercel**, guia "Connection Pooling with Vercel Functions": `attachDatabasePool` fecha as conexões ociosas antes de suspender a instância, e o guia recomenda idle timeout curto (~5 s).
- **Prisma v7**, doc de connection pool: o `pg` tem `max` 10, `idleTimeoutMillis` 10 s e **`connectionTimeoutMillis` 0, que significa esperar para sempre**. O `PrismaPg` 7.10.0 aceita um `pg.Pool` pronto, conferido no `index.d.ts` do pacote.
- **Neon**, "Scale to Zero": no Free, o banco desliga após **5 min** sem uso (fixo) e acorda em "algumas centenas de ms".
- **Upstash:**
  - o Free tem **500 mil comandos por mês**;
  - o `@upstash/ratelimit` deixa passar após o `timeout` (padrão de **5 s**, com `reason: "timeout"`).
- **Vercel** sobrescreve o `x-forwarded-for` (IP não é forjável). Para ler o IP: `ipAddress()` de `@vercel/functions`.

| # | Decisão | Escolha | Registrada em |
|---|---|---|---|
| 9a | Desativar pode ser desfeito? | **Não, e com passo de confirmação** na página. Sem `reactivateLink`, porque o token vazado só "vê e desativa, nunca sequestra". Descartados: reversível e um clique só | `domain.md` |
| 9b | Desativar um link já desativado | **Sucesso idempotente, mantendo a data original** (`UPDATE … WHERE deactivated_at IS NULL`; sem linha afetada, busca pelo hash para distinguir token inválido de "já desativado"). Regra fixa: identificar **pelo token**, nunca pelo slug (IDOR, OWASP API1:2023) | `domain.md` |
| D1 | Driver adapter | **`@prisma/adapter-pg`** + `pg.Pool` global + **`attachDatabasePool`** (`@vercel/functions`), com `idleTimeoutMillis: 5000`. Descartado: `@prisma/adapter-neon` | `architecture.md` |
| 10a | Upstash fora do ar | **Redirect: fail-open. Criação: fail-closed.** Na criação, `reason === "timeout"` conta como falha | `security.md` |
| 10b | Números do rate limit | **Criação: 10/min e 100/dia por IP. Redirect: 300/min por IP.** Janela deslizante, timeout da lib de **1 s**, `429` com `Retry-After` | `security.md` |
| 10c | Chave no IPv6 | **Prefixo `/64`** (os últimos 64 bits são escolhidos pelo aparelho, RFC 4291 e RFC 8981). `::ffff:` tratado como IPv4. Função pura, sem lib | `security.md` |
| 10d | Colisão de slug | **Até 3 tentativas**, detectadas no `INSERT` (`P2002`), nunca "consulta e depois grava". 3 colisões seguidas = defeito, logado como erro | `domain.md` |
| 10e | Timeout do banco | **`connectionTimeoutMillis: 5000`**; estourou → `503` com `Retry-After` no redirect, erro na criação. Descartados: sem timeout e 1 s (falharia ao acordar o Neon) | `architecture.md`, `domain.md` |
| — | Mapa de erros | Tabela aprovada: `fieldErrors` por campo, `message` geral, gestão e `deactivateLink`. Token fora do formato → `404` sem banco. Página de gestão **sem rate limit** (token de 256 bits) | `domain.md`, "Mapa de erros" |

**Defeito corrigido (2026-09-30):** o SQL atômico de referência **não checava `deactivated_at`**, então um link desativado continuaria redirecionando. Ele também usava a coluna `original_url` (o schema chama `destination_url`) e não devolvia o `id`, que o `after()` precisa. Corrigido em `domain.md`, "Incremento atômico".

**Outros ajustes:**
- os fluxos de criação e de redirect no `domain.md` agora mostram rate limit, fail-open/closed, colisão, `429` e `503`;
- o módulo de templates HTML também gera o `429` e o `503`.

**Pauta aberta: P1 a P7.** Levantados pelo agente; o Rafael quer debater **todos, um por mensagem, começando pelo P1**. **Nada disto foi decidido ainda.**

| # | Cenário | Tipo proposto |
|---|---|---|
| P1 | **Falha depois de gravar:** o link é gravado e só depois o QR é gerado. Se o QR falhar e a action devolver erro, o token (exibido uma vez só) se perde, e o link fica órfão. Hipótese a debater: `qrCodeDataUrl` opcional (`string \| null`) no estado de sucesso | ✅ **B** (2026-09-30): sucesso parcial com `qrCodeDataUrl: null`; ver `domain.md`. **P1b: C**: QR também na página de gestão (`domain.md`, `architecture.md`, PRD) |
| P2 | **Parâmetros no link curto:** `/aB3xZ9k?utm_source=instagram` é repassado ao destino ou ignorado? | ✅ **A** (2026-09-30): ignorar; ver `domain.md`. Dica para o README: "um link por canal", com UTM no destino |
| P3 | **Duplo clique no "Encurtar"** criaria 2 links. Proposta: botão desabilitado enquanto `isPending` (`useActionState`) | ✅ **B** (2026-09-30): botão desabilitado com `isPending`; ver `domain.md` |
| P4 | **Espaços colados junto com a URL.** Proposta: `trim()` na entrada antes de validar | ✅ **B** (2026-09-30): `trim()` nas pontas de todos os campos; ver `domain.md` |
| P5 | **Resposta perdida na rede** depois de gravar: o token se perde, e o usuário cria outro. Sem conta, não há como recuperar | ✅ **B + C** (2026-09-30): destaque no card + `beforeunload` até copiar o link de gestão; perda na rede documentada. Ver `domain.md` |
| P6 | **Domínio "sósia" (homógrafo)**, ex.: `аpple.com` com "а" cirílico. O `new URL()` converte para punycode (`xn--…`). Bloquear exigiria blocklist (na época fora de escopo; depois virou a R7, seção 2e) | ✅ **A** (2026-09-30): aceitar e documentar (o Chrome mostra punycode); recusar mistura de alfabetos é evolução. Ver `domain.md` |
| P7 | **"Até o fim de hoje" escolhido às 23h50:** o link dura 10 min. Comportamento correto, mas pouco intuitivo | limitação a documentar |

**Situação da pauta P:** P1 a P6 ✅ decididos e commitados (`bfe5fad`). **Falta o P7**, que fica para depois das decisões B1 a B3 da seção 2e.

### 2e. Blocklist no MVP (decidido em 2026-09-30)

O Rafael perguntou se valia incluir a blocklist, que o PRD deixava como evolução. Foi feita uma análise com varredura dos arquivos, e ele **decidiu incluí-la no MVP** como **regra R7**. Motivos:
- protege quem clica;
- protege **o próprio domínio da demo**, que poderia ser marcado como perigoso por navegadores e filtros de e-mail se redirecionasse para golpes (o recrutador veria a tela vermelha);
- é um bom assunto de entrevista.

**Como ficou (registrado em `domain.md` R7, `security.md` "Blocklist", `architecture.md` e PRD):**
- **Só na criação**, depois de R1 a R6. O redirect não muda e não faz consulta externa.
- **Google Safe Browsing v5, `hashes.search`** (modo "No-Storage Real-Time"). O adaptador envia **só prefixos de 4 bytes do SHA-256**, nunca a URL; a comparação final é local. A parte trabalhosa é a **canonicalização da URL** conforme a spec do Google, coberta com testes de tabela usando os exemplos da documentação.
- **Porta do domínio `UrlThreatChecker`**, injetada no `LinkService` (mesmo padrão do `LinkRepository`), com fake em memória nos testes. **Sem dependência nova** (`fetch` e `crypto.subtle` nativos). A arquitetura não muda.
- **Custo: gratuito**, conferido nas docs "Pricing" e "Usage Restrictions". Termos de **uso não comercial**; se virar produto pago, trocar o adaptador pelo Google Web Risk.
- **Cota:** a documentação não publica o número; ele aparece no Cloud Console depois de ativar a API, e o aumento pode ser pedido sem custo. Terceiros citam 10 mil por dia (não oficial). O consumo é baixo, porque só a criação consulta, e ela é limitada a 100 por dia por IP.
- **Configuração (o Rafael faz, antes da implementação):** conta Google → projeto no Google Cloud Console → API key → ativar a "Safe Browsing API". O passo a passo não pede faturamento. **Restringir a key à Safe Browsing API** no console.
- **Segredo novo:** `SAFE_BROWSING_API_KEY`, só no servidor. A key vai na query string da chamada ao Google, então **nunca logar a URL dessa requisição**.
- **Atribuição obrigatória** ao bloquear: "Advisory provided by Google", com link para o Safe Browsing Advisory (doc "Appropriate Usage").
- **Fora do MVP (evolução):** reverificação periódica dos links já criados; recusar mistura de alfabetos (P6).
- Descartados: `urls.search` (envia a URL e é alfa), Web Risk (envia a URL e é comercial) e URLhaus (malware, não phishing).
- **ADR:** não muda, porque não passa no critério "difícil de reverter".

**Pendentes da blocklist (próximas decisões, uma por mensagem):**

| # | Decisão | Contexto |
|---|---|---|
| B1 | Safe Browsing fora do ar, lento ou com cota esgotada | Fail-open (cria sem checar) ou fail-closed (recusa a criação, como no rate limit da 10a)? Timeout da chamada |
| B2 | Pasta do adaptador | `src/infra/` (integrações externas) ou dentro de `src/data/`, que hoje é "o único lugar que importa Prisma" |
| B3 | Mensagem de bloqueio | Texto em pt-BR, posição da atribuição "Advisory provided by Google" e o link. A linha no mapa de erros do `domain.md` está como "a decidir" |

**Pendente visual:** no Excalidraw, a seção SYSTEM DESIGN precisa de uma caixa externa "Google Safe Browsing" ligada ao domínio (só com o pedido explícito do Rafael, ver "What Didn't Work").

### 3. Documentação visual no Excalidraw

Está no localStorage do Chrome do Rafael (excalidraw.com). **Ainda não foi exportada para o repositório.** Seções, de cima para baixo, cada uma com um rótulo à esquerda e uma moldura:

1. **STACKS:** tabela desenhada no mesmo estilo das tabelas do modelo de dados, com cabeçalho lilás "Camada / Escolha", 11 linhas **já com as versões da baseline** e rodapé apontando para `architecture.md`. Substituiu a imagem colada em 2026-09-28.
2. **SYSTEM DESIGN:**
   - fluxo Navegador → Vercel Edge → Next.js;
   - `RateLimiter` como faixa-guarda no topo da camada de entrada, ligado ao Upstash à direita por uma seta horizontal;
   - domínio com `«interface» LinkRepository` e dados com `PrismaLinkRepository`, com a seta tracejada "implementa";
   - seta dados → Neon com o rótulo "Prisma 7 — SQL parametrizado / via driver adapter";
   - Neon abaixo da camada de dados, com a linha "pooled (app) · direct (migrations)";
   - bloco **DECISÕES DE DESIGN** com 8 itens.
3. **MODELO DE DADOS:** diagrama ER com `links` e `click_events` (1:N em crow's foot, `ON DELETE RESTRICT`), `«enum» device_type` (já com `BOT`, seta tracejada rotulada "tipo da coluna device_type") e **NOTAS DO MODELO** com 8 itens (o item 8 já traz a decisão dos bots).
4. **REGRAS DE NEGÓCIO:** 10 regras em linguagem acessível a leigos, com o rodapé "Versão técnica, com as justificativas: .agents/context/domain.md e docs/superpowers/PRD.md".
   - *Opcional, ainda não feito:* a regra 6 só fala em "http:// ou https://". As regras R2 a R4 (credenciais na URL, próprio domínio, rede interna), o limite de 1 a 1.000.000 e a expiração por duração ou fim do dia não aparecem. Oferecer ao Rafael quando o Excalidraw for editado de novo, por exemplo junto da seção RF/RNF.

**Combinado com o Rafael:**
- O Excalidraw é o **resumo visual**, e a fonte da verdade são os arquivos Markdown.
- A seção de **RF/RNF** entra **só depois de a spec ser aprovada**, com os IDs da tabela `## Requisitos rastreados`.
- No fim, o **Rafael exporta** manualmente (*Save to…* → `.excalidraw`; *Export image* → SVG) para `docs/`. O agente não consegue tirar o arquivo do navegador com a imagem embutida.
- Backups no localStorage: chaves `excalidraw-backup-<timestamp>`. Os mais recentes são `excalidraw-backup-1790616184133` (anterior à troca identity → serial) e `excalidraw-backup-1790613645597` (anterior à troca da imagem STACKS).
- ✅ **E4 aplicado em 2026-09-28:** as colunas de tipo do MODELO DE DADOS mostram `int · serial` (`links`) e `bigint · bigserial` (`click_events`). A cena tem 93 elementos, porque o Excalidraw descartou a imagem excluída ao salvar.

## What Worked

- **Formato das decisões que funcionou em 2026-09-29** (o Rafael aprovou: "beeem melhor assim"):
  1. um **cenário concreto** ("a Maria clica num link que expirou…");
  2. cada opção A/B/C em **1–2 frases**, com uma **mini linha do tempo** ou um exemplo (`clique → conta → Maria vai pro destino → anota`);
  3. uma **tabela curta em linguagem simples**, sem jargão sem explicação;
  4. a recomendação em poucas linhas e uma fonte numa linha só.
  
  Verificação de fontes, roteiros e subdecisões futuras ficam **fora** da mensagem da decisão.
- **Quando o Rafael pede "explique mais a fundo" depois de decidir** (10b e 10e, em 2026-09-30), funcionou assim:
  1. uma **analogia do cotidiano** (caixa eletrônico para o rate limit, ligar para um restaurante para o timeout);
  2. **situações numeradas** (dia normal / banco dormindo / banco fora do ar) com a mesma linha do tempo para A, B e C lado a lado;
  3. uma **tabela resumo** "situação × opção" com ✓/✗.
  
  Ele esclareceu que não é crítica à explicação: quer entender a fundo porque está aprendendo e montando portfólio. Explique com paciência e sem repetir o jargão.
- **Revisar os documentos procurando defeitos antes da spec.** Ao reler o `domain.md` para listar cenários faltantes, apareceu o SQL atômico sem `deactivated_at`. Vale uma releitura crítica de cada regra antes de escrever a spec.
- **Debater cada decisão isoladamente, com opções A/B/C, tabela de trade-offs, fonte primária e recomendação.** O Rafael pediu isso explicitamente: ele não escolhe sem entender os prós e contras. Uma decisão por mensagem. Ao final, registrar a decisão no arquivo certo **na hora**, para não perder se a sessão cair.
- **Analogias com Java/Spring e JPA** (`@OneToMany`/`@ManyToOne`, `@Column(unique = true)`, `@Enumerated`, `Filter`) e exemplos de código curtos.
- **Verificar fatos de biblioteca antes de afirmar:** context7 para o Prisma (`updateManyAndReturn` desde a 6.2.0, `uuid(7)` desde a 5.18.0) e firecrawl para o OWASP. A documentação do Prisma já mostra a **v7**, então é preciso fixar a versão no setup.
- **Verificar versões direto na fonte:** `npm view <pkg> dist-tags` pegou a armadilha do Prisma 8 RC, e ler o `peerDependencies` do `typescript-eslint` pegou a incompatibilidade com o TS 7. Explicações curtas com exemplo concreto (erro real, URL real, analogia com JDBC/HikariCP) funcionaram melhor que texto longo: o Rafael pediu **menos verbosidade e mais exemplos**.
- **Edição do Excalidraw via localStorage** (claude-in-chrome). ⚠️ **Só grave quando o Rafael pedir na própria mensagem**, porque o classificador bloqueia do contrário (ver What Didn't Work). O passo 2 abaixo (neutralizar o `setItem`) é **negado** pelo classificador. O que funcionou em 2026-09-28: aba sem interação com o canvas → conferir a contagem → backup → gravar `excalidraw` e `version-dataState` → fechar → reabrir e verificar. O protocolo original fica como referência:
  1. **O Rafael fecha TODAS as abas do excalidraw.com** e confirma com "fechei".
  2. O agente abre uma aba, e **logo após o load neutraliza `Storage.prototype.setItem`** para as chaves `excalidraw*` e `version*`, guardando o original em `window.__origSetItem`.
  3. Relê a cena, confere a contagem de elementos (e aborta se mudou) e **identifica os elementos por conteúdo de texto**, nunca por posição, porque o Rafael reorganiza o quadro entre as sessões.
  4. Faz um *dry run* com as métricas (tudo cabe na moldura?) e depois grava: backup em `excalidraw-backup-<ts>`, `excalidraw` e `version-dataState = Date.now()`, todos pelo `setItem` original.
  5. Relê para confirmar, fecha a aba e **só então** avisa o Rafael que ele pode abrir.
- **Técnicas do script:**
  - Medir o texto com `canvas.measureText` na fonte `Excalifont` (lineHeight 1.25).
  - Clonar elementos existentes para herdar o estilo.
  - Usar `index` fracionário = maior índice existente + `'V' + letras`.
  - Envolver o código numa IIFE (`(() => {...})()`) para poder rodar de novo na mesma aba.
- **Crow's foot existe** nesta versão do Excalidraw (`crowfoot_one` e `crowfoot_many`). Foi verificado buscando a string nos bundles JS carregados.

## What Didn't Work (não repetir)

- **Deixar edições sem commit por muito tempo.** Em 2026-09-30, um Ctrl+Z no editor do Rafael desfez parte das edições do `domain.md` (respostas 429/503, mapa de erros, correção do SQL), que ainda não tinham sido commitadas. Tudo foi refeito a partir do histórico da conversa. **Commite ao fim de cada bloco de decisões** (e confira `git diff --stat` antes de retomar).
- **Mensagem de decisão densa** (2026-09-29, primeira versão da 7a). Abria com uma tabela de verificação de fontes, um diagrama do fluxo e um roteiro de subdecisões, e as opções vinham em jargão ("CTE", "waitUntil", "round trip") dentro de células cheias. O Rafael respondeu: "não entendi nada… verbosa, confusa e nada explicativa". Use o formato de "What Worked".
- **Gravar no localStorage com a aba do Rafael aberta.** Qualquer interação na aba dele, até rolar a roda do mouse sem dar foco à janela, dispara o salvamento automático e grava por cima a cena antiga que está em memória. Recarregar com F5 também grava por cima. **Sempre fechar primeiro.**
- **O Rafael reabrir antes de o agente gravar.** A aba nova carrega o estado antigo. A ordem certa é **fechar → agente grava → agente avisa → abrir**.
- **Imprimir IDs de elementos no retorno do `javascript_tool`.** O filtro de saída bloqueia com "[BLOCKED: Cookie/query string data]". Use índices ou conteúdo, nunca IDs. Saídas longas são truncadas, então pagine.
- **Buscar texto por prefixo quando há colisão.** `startsWith('LinkService')` também casou com a nota "LinkService recebe...". Use igualdade exata onde houver risco.
- **Clicar, arrastar ou tirar screenshot da aba MCP em segundo plano.** Ela não renderiza (o `requestAnimationFrame` fica pausado).
- **Gravar no Excalidraw sem autorização explícita do Rafael.** Em 2026-09-28, o classificador negou a neutralização do `Storage.prototype.setItem` ("Irreversible Local Destruction") e, depois, uma reabertura do excalidraw.com para gravar que o Rafael não tinha pedido naquela mensagem ("Auto-Mode Bypass"). Quando o Rafael pediu a edição explicitamente ("pode editar no excalidraw já"), a gravação passou. **Regra:** só grave quando ele pedir na própria mensagem, e nunca tente rotas alternativas depois de uma negação.
- **Assumir que a contagem de elementos não muda.** Ao salvar, o Excalidraw descarta os elementos com `isDeleted` (foi de 94 para 93). Se a contagem mudar, verifique se a diferença é só isso (contagem de vivos e `updated` máximo) antes de gravar.
- **Screenshot da aba MCP:** deu timeout ("renderer frozen") mesmo com um overlay de imagem. Para ver uma imagem da cena, peça ao Rafael.
- **Terminar um turno sem resposta.** Na sessão anterior, uma resposta saiu vazia e o Rafael achou que havia perguntas perdidas.

## Next Steps

Na ordem do processo arquitetural do `superpowers:brainstorming`:

1. **Rotas e contratos** (próximo passo). Para cada um, definir entrada, saída, códigos HTTP e validação:
   - ✅ **Server Action `createLink` fechada em 2026-09-28** (tudo em `domain.md`):
     - **6a:** regras R1 a R6 da URL de destino. `http:` é aceito, com aviso na criação;
     - **6b:** limite de cliques de 1 a 1.000.000; expiração por duração pronta (1 h, 24 h, 7 dias, 30 dias) ou fim do dia em `America/Sao_Paulo`, com máximo de 5 anos;
     - **6c:** token em base64url (43 caracteres), estado discriminado `CreateLinkState` (Server Action não tem status HTTP de erro), exibição única num card na tela de criação (sem redirect para `/manage`) e QR em PNG de 512 px. Nota: o `qrcode@1.5.4` traz `yargs@15`; reavaliar na spec;
   - ✅ **Route Handler `GET`/`HEAD /[slug]` fechado em 2026-09-29** (decisões 7a a 7e; ver seção 2c);
   - ✅ **Page `/manage/[token]` fechada em 2026-09-29** (8a: janela de 30 dias; 8b: token no path + headers);
   - ✅ premissas `after()` e CSRF das Server Actions verificadas;
   - ✅ **Server Action `deactivateLink` fechada** (9a: irreversível com confirmação; 9b: idempotente, pelo token);
   - ✅ **D1: `@prisma/adapter-pg` + `attachDatabasePool`** (seção 2d).
2. ✅ **Tratamento de erros** fechado em 2026-09-30: 10a a 10e e o mapa de erros (seção 2d).
   - ✅ pauta P1 a P6 (seção 2d);
   - ✅ blocklist incluída no MVP como R7 (seção 2e);
   - **Próximo: B1 → B2 → B3** (seção 2e) **→ P7** (seção 2d), um por mensagem.
3. **Estratégia de testes:**
   - ferramenta (ex.: Vitest);
   - domínio com fakes em memória;
   - funções puras (`classifyDevice`, `extractReferrerHost`, `isPreviewBot`, `SlugGenerator`) com tabela de casos;
   - o **incremento atômico sob concorrência** precisa de teste com Postgres real (o D1 usa `pg`, que funciona com Postgres local em Docker);
   - candidatos a teste de tabela surgidos em 2026-09-29/30: normalização do IP para `/64` (10c), `isValidSlugFormat` (7e), formato do token (mapa de erros), precedência do motivo do 410 (7d), retry de colisão (10d), fail-open/closed (10a) com fake do rate limiter, `trim()` (P4) e **canonicalização do Safe Browsing (R7)**, com os exemplos da documentação do Google como tabela de casos;
   - R7 no domínio com fake do `UrlThreatChecker` (seguro, perigoso, fora do ar).
4. **Escrever a spec:**
   - arquivo `docs/superpowers/specs/2026-09-XX-short-url-mvp-design.md`, no formato de `.agents/rules/spec-workflow.md`: cabeçalho Data/Status/Branch Alvo, seções numeradas, `## Alternativas consideradas e por que foram descartadas` e `## Requisitos rastreados` com RF/RNF;
   - consolidar tudo de `domain.md`, `security.md`, `architecture.md` e PRD, incluindo a nota sobre o AD-004 e o QR;
   - incluir os itens de setup que vieram da baseline e do npm: `.npmrc` com `save-exact=true`, `min-release-age=1` e `strict-allow-scripts=true`, `allowScripts` no `package.json`, regra `import/no-extraneous-dependencies`, `engines.node`, o script `prisma generate && next build`, o `.env.example` com `DATABASE_URL`, `DIRECT_URL`, os tokens do Upstash e a `SAFE_BROWSING_API_KEY`, e instalação sempre com versão explícita;
   - pré-requisito externo: o Rafael cria o projeto no Google Cloud e a API key restrita à Safe Browsing API (seção 2e);
   - adicionar a linha em `specs/README.md`;
   - autorrevisão;
   - pedir a revisão do Rafael.
5. Com a spec aprovada:
   - adicionar a seção **RF/RNF** no Excalidraw (ver o bloqueio do classificador em What Didn't Work);
   - invocar **`superpowers:writing-plans`**;
   - só depois do plano aprovado, escrever código.

### Ainda em aberto (resolver nos passos acima)
A ordem combinada com o Rafael é **uma decisão por mensagem**. A pauta é: ~~1. baseline de versões~~ (✅ 2026-09-28) → ~~2. gerenciador de pacotes~~ (✅ npm 11 endurecido, ver `architecture.md`) → ~~3. convenção de nome de arquivo~~ (✅ kebab-case, ver `code-style.md`) → ~~4. idioma da interface~~ (✅ pt-BR na UI e no README, ver PRD) → ~~5. `git init` e padrão de commit~~ (✅ Conventional Commits, descrição em pt-BR, trailer do Claude mantido; ver `code-style.md`) → **Next Steps (rotas e contratos)**.

- **Técnicas:**
  - ~~versões de Node, Next.js e Prisma~~: ✅ resolvido (seção 2b);
  - ~~gerenciador de pacotes~~: ✅ **npm 11**, com `.npmrc` (`save-exact`, `min-release-age=1`, `strict-allow-scripts`), `allowScripts` no `package.json` e a regra de lint `import/no-extraneous-dependencies` contra dependência fantasma. O pnpm 11 foi descartado porque a Vercel só documenta até o pnpm 10;
  - ~~D1, driver adapter~~: ✅ `@prisma/adapter-pg` + `attachDatabasePool` (seção 2d);
  - ~~convenção de nome de arquivo~~: ✅ kebab-case em tudo (`code-style.md`);
  - ~~padrão de commit~~: ✅ ver `code-style.md`.
- ~~**Produto:** idioma da interface~~: ✅ pt-BR na UI e no README. O alvo atual são vagas no Brasil; i18n ficou fora de escopo, com o motivo no PRD.
- **Repositório:** ✅ público em **https://github.com/ribeirorafadev/url-shortener** (remoto `origin` via SSH, `git@github.com:ribeirorafadev/url-shortener.git`; o SSH da máquina já está autenticado como `ribeirorafadev`). `main` está sincronizada com `origin/main`, só com commits de documentação. Confira o último com `git log --oneline -3`. A spec será commitada na branch dela (ex.: `feat/mvp`).
  - **Push:** só com autorização explícita do Rafael na mensagem.
  - **"About" do GitHub:** ✅ configurado pelo Rafael (descrição e topics). O MCP do GitHub não edita metadados de repositório, e o `gh` e a CLI `vercel` não estão instalados.
  - **README:** ainda não existe. O completo é entrega do PRD, no fim. Um README curto provisório foi oferecido e fica a critério do Rafael.
  - **Repositório público:** tudo o que é commitado fica visível, inclusive este HANDOFF. A varredura de 2026-09-28 não encontrou segredos nem dados pessoais. O `.gitignore` foi reorganizado por seções, e a política do `.npmrc` sem token e dos artefatos de teste ignorados está em `security.md`.

## Preferências do Rafael relevantes para a sessão

- Português (pt-BR), direto e sem floreio. Markdown estruturado e **negrito** em termos críticos.
- Decisão não trivial precisa citar fonte real (doc oficial, RFC, lei, OWASP).
- Quer **entender os trade-offs antes de decidir**. Nunca apresente uma decisão como fato consumado.
- Explicações **objetivas, com exemplo concreto** (erro real, trecho de código, analogia com Java/Spring). Quando algo não fica claro, ele pede para reexplicar antes de avançar: explique, depois siga.
- Ao fechar um bloco de decisões, costuma pedir **varredura dos arquivos afetados + atualização do HANDOFF**. Faça a varredura com `grep` pelos termos da decisão, não de memória.
- Tem base em Java/Spring e em segurança, e está aprendendo Next.js, ORM e serverless agora.
- Antes de ação destrutiva: primeiro um relatório (o quê, onde, risco), depois a autorização explícita.
- Pode acionar o Antigravity CLI (`agy -p "..."`) para pesquisa web ou revisão.
