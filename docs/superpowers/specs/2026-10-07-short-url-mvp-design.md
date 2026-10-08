# short-url MVP — Especificação de Design

**Data:** 2026-10-07  
**Status:** Aprovada (2026-10-08)  
**Branch Alvo:** `feat/mvp-1-base` · `feat/mvp-2-create-redirect` · `feat/mvp-3-manage` (uma por fatia, ver §12)

> **Como ler.** Esta spec guarda **o como**: tipos, assinaturas, SQL, nomes de arquivo, configuração e plano de testes. **O quê e o porquê** (regras, motivos, alternativas descartadas em detalhe) continuam em `.agents/rules/` e `.agents/context/`, e cada seção começa apontando para eles. Critério de `spec-workflow.md` §8: se mudar durante a implementação e a regra de negócio não mudar, é daqui. Nomes de API marcados **(conferir na tarefa)** foram lidos na documentação, mas só o teste da tarefa prova o comportamento.

## 1. Contexto

Encurtador de links com analytics, primeiro projeto do portfólio full-stack do Rafael, em Node.js/TypeScript. Problema, público, escopo, fora de escopo e critério de "pronto" estão em `docs/superpowers/PRD.md`. Decisões de base: AD-001 (Next.js único na Vercel), AD-002 (Prisma + Neon), AD-003 (sem login, token de gestão) e AD-004 (domínio em TypeScript puro), em `docs/superpowers/ADR.md`.

O design foi fechado em sessões de 2026-09-23 a 2026-10-07, com uma releitura crítica (RC1 a RC10, B-1 a B-4) e as lacunas S1 a S5 achadas ao preparar esta spec. O índice das decisões fica no `HANDOFF.md`; cada uma está registrada no arquivo-fonte com rótulo e data.

## 2. Objetivo e critério de "pronto"

Entregar, em três fatias publicadas uma a uma, o fluxo **criar → compartilhar → clicar → ver estatísticas → desativar**, com o critério de "pronto" do PRD integralmente atendido. A §16 liga cada requisito à fatia que o entrega.

## 3. Escopo

Exatamente o "Escopo do MVP" do PRD, sem cortes. O "Fora de escopo" do PRD vale como lista de evoluções documentadas (README, seção "como escalaria").

## 4. Arquitetura

Regras: `.agents/rules/architecture-layers.md` (núcleo), AD-004.

### 4.1 Pastas e arquivos

```
.
├── .github/workflows/ci.yml
├── .npmrc                         → §9.2
├── components.json                → configuração do CLI do shadcn/ui
├── compose.yml                    → §9.7
├── docker/postgres-init.sql       → cria o banco de teste (§9.7)
├── eslint.config.mjs              → §9.3
├── eslint.config.test.ts          → §9.3 (prova permanente das regras de import)
├── next.config.ts                 → §9.4
├── next.config.test.ts            → §9.4 (travas e headers)
├── postcss.config.mjs             → Tailwind 4 (@tailwindcss/postcss)
├── prisma.config.ts               → §9.5
├── prisma/schema.prisma           → §6.1
├── prisma/migrations/
├── vercel.json                    → §9.6
├── vitest.config.mts              → §9.8 (unit + integração)
├── vitest.http.config.mts         → §9.8 (testes HTTP)
├── tests/http/                    → §11 (testes HTTP; global-setup.ts e helpers/database.ts)
├── tests/setup/integration-setup.ts → §9.8 (trava de host e TRUNCATE)
├── .env.example                   → §9.9
└── src/
    ├── app/
    │   ├── layout.tsx · page.tsx · not-found.tsx · globals.css
    │   ├── actions/create-link.ts         → §8.3 (Server Action)
    │   ├── actions/deactivate-link.ts     → §8.5 (Server Action)
    │   ├── [slug]/route.ts                → §8.4 (GET e HEAD)
    │   ├── manage/[token]/page.tsx        → §8.5
    │   └── _lib/
    │       ├── services.ts                → §4.3 (ponto de montagem)
    │       ├── app-origin.ts              → §8.1
    │       ├── client-ip.ts               → §8.2 (chave /64)
    │       ├── rate-limit.ts              → §8.2 (porta, números, adaptadores)
    │       ├── create-link-form.ts        → §8.3 (rodada de formato)
    │       ├── create-link-state.ts       → §8.3 (tipo e mapeamento de erros)
    │       ├── create-link-handler.ts     → §8.3 (orquestra a criação)
    │       ├── redirect-handler.ts        → §8.4 (orquestra o redirect)
    │       ├── manage-page-loader.ts      → §8.5 (carrega a gestão)
    │       ├── manage-labels.ts           → §8.5 (textos da gestão)
    │       ├── deactivate-link-handler.ts → §8.5 (orquestra a desativação)
    │       ├── status-pages.ts            → §8.6 (HTML fixo)
    │       ├── qr-code.ts                 → §8.3
    │       └── log.ts                     → §4.4
    ├── components/
    │   ├── ui/                            → shadcn/ui (button, input, label, card, alert)
    │   ├── create-link-form.tsx           → 'use client'
    │   ├── expiration-field.tsx           → 'use client' (rótulo da P7)
    │   ├── expiration-label.ts            → §8.3 (cálculo do rótulo da P7, puro)
    │   ├── link-result-card.tsx           → 'use client' (copiar, baixar, beforeunload)
    │   ├── deactivate-link-form.tsx       → 'use client' (passo de confirmação)
    │   └── daily-clicks-chart.tsx         → Server Component (S5)
    ├── lib/utils.ts                       → cn() do shadcn/ui
    ├── domain/                            → §5 (sem nenhum import de pacote)
    │   ├── link.ts · ports.ts · errors.ts
    │   ├── slug.ts · manage-token.ts · sao-paulo-time.ts
    │   ├── url-validator.ts · click-tracker.ts · preview-bot.ts
    │   ├── link-service.ts · redirect-service.ts · click-stats.ts
    ├── data/                              → §6 (único lugar com Prisma)
    │   ├── prisma-client.ts
    │   ├── prisma-link-repository.ts
    │   ├── prisma-click-event-repository.ts
    │   ├── database-errors.ts
    │   └── generated/prisma/              → gerado no postinstall, fora do Git
    └── infra/                             → §7
        ├── safe-browsing-url-threat-checker.ts
        ├── safe-browsing-expressions.ts   → canonicalização e expressões (puro)
        ├── local-fake-url-threat-checker.ts
        └── unavailable-url-threat-checker.ts
```

Os testes ficam ao lado do arquivo testado (`link-service.test.ts`); os de integração com Postgres usam o sufixo `.int.test.ts`, e os HTTP ficam em `tests/http/*.http.test.ts`. Fakes e auxiliares de teste (ex.: os repositórios em memória da §11) ficam em `__fakes__/` ao lado do código (`src/domain/__fakes__/`: `InMemoryLinkRepository`, `InMemoryClickEventRepository`, `ProgrammableThreatChecker`, `FixedClock`); a trava do executor protege essa pasta, como protege os testes (`.agents/rules/execution-workflow.md`, D4).

**Entrada fina (`architecture-testing-ci.md`):** `route.ts`, `page.tsx` da gestão e as Server Actions só montam as dependências reais e chamam um *handler* ou *loader* de `src/app/_lib/` que recebe tudo por parâmetro e é testado no Vitest sem servidor.

**Rotas fixas na raiz:** só `/manage` (6 caracteres). Nenhuma rota fixa nova pode ter exatamente 7 caracteres `[A-Za-z0-9]` (B-4, `redirect.md`).

### 4.2 Direção das dependências

`app` → `domain` ← `data` e `infra`. O domínio só usa globais nativos (`crypto.getRandomValues`, `crypto.subtle`, `TextEncoder`, `URL`, `Intl`, `btoa`). O lint transforma isso em erro (S2, §9.3).

### 4.3 Ponto de montagem (`src/app/_lib/services.ts`)

Único lugar que instancia adaptadores e serviços. Funções preguiçosas, memoizadas por instância da função (Fluid compute reaproveita a instância):

```ts
export function getLinkService(): LinkService
export function getRedirectService(): RedirectService
export function getClickEventRepository(): ClickEventRepository
export function getRateLimiter(): RateLimiter
export function getUrlThreatChecker(): UrlThreatChecker // usado pelo getLinkService; exposto para o teste
```

- O `UrlValidator` do `getLinkService` recebe `resolveAppOrigin(process.env)?.ownHosts ?? []`. Sem origem, a action da criação recusa antes de chamar o `create` (§8.3, passo 2), então a lista vazia nunca chega a validar uma URL.

- **Nenhum módulo abre conexão ou cria cliente externo no import.** O `next build` não precisa de banco nem de chave.
- **Falsos locais (trava 1, `architecture-local-dev.md`):** `useLocalFakes = process.env.NODE_ENV === 'development' && process.env.USE_LOCAL_FAKES === 'true'`. Com ele, injeta `LocalFakeUrlThreatChecker` e `InMemoryRateLimiter`.
- **Configuração ausente ou inválida (RC4, `security-rate-limit.md`):** antes de criar cada cliente, confere a variável (`UPSTASH_REDIS_REST_URL` como URL `https:`, `UPSTASH_REDIS_REST_TOKEN` e `SAFE_BROWSING_API_KEY` não vazias) e envolve a criação em `try/catch`. Falhou → injeta `UnavailableRateLimiter` ou `UnavailableUrlThreatChecker` e loga uma vez por instância (`config-missing`, com o nome da variável, nunca o valor).
- O `Clock` de produção é `{ now: () => new Date() }`.

### 4.4 Logs (`src/app/_lib/log.ts`)

`logError(event: LogEvent, fields?: SafeLogFields)` e `logWarn(...)` escrevem uma linha JSON no `console.error`/`console.warn` (a Vercel coleta o stdout/stderr). `SafeLogFields` é uma lista branca de chaves: `slug`, `reason`, `errorName`, `variable`, `status`. **Nunca** entram token, hash do token, URL de destino, IP, user-agent nem a URL da chamada ao Google (leva a API key). `LogEvent` é uma união de literais (`'click-event-failed' | 'qr-failed' | 'rate-limiter-unavailable' | 'threat-checker-unavailable' | 'slug-collisions' | 'app-origin-missing' | 'config-missing' | 'database-unavailable' | 'unexpected-error'`).

## 5. Domínio (`src/domain/`)

Regras: `.agents/context/link-lifecycle.md`, `url-validation.md`, `link-creation.md`, `redirect.md`, `manage-page.md`, `data-model.md`; `.agents/rules/security-token.md`.

### 5.1 Tipos (`link.ts`)

```ts
export type DeviceType = 'MOBILE' | 'DESKTOP' | 'TABLET' | 'BOT' | 'UNKNOWN'
export type GoneReason = 'deactivated' | 'expired' | 'exhausted'
export type ExpirationDuration = '1h' | '24h' | '7d' | '30d'

export type ExpirationChoice =
  | { kind: 'none' }
  | { kind: 'duration'; duration: ExpirationDuration }
  | { kind: 'end-of-day'; date: string } // 'YYYY-MM-DD', data de calendário válida

export interface LinkSnapshot {
  id: number
  slug: string
  destinationUrl: string
  clickCount: number
  maxClicks: number | null
  expiresAt: Date | null
  deactivatedAt: Date | null
  createdAt: Date
}

export interface NewLink {
  slug: string
  destinationUrl: string
  manageTokenHash: Uint8Array
  maxClicks: number | null
  expiresAt: Date | null
}

export const EXPIRATION_DURATION_MS: Record<ExpirationDuration, number> // 1 h, 24 h, 7 d, 30 d
export const MAX_CLICKS_RANGE = { min: 1, max: 1_000_000 } as const
export const MAX_URL_LENGTH = 2048
export const MAX_EXPIRATION_YEARS = 5
```

`classifyLink(link: LinkSnapshot, now: Date): 'active' | GoneReason` aplica a precedência **desativado → expirado → esgotado** (`redirect.md`): `deactivatedAt !== null` → `'deactivated'`; `expiresAt !== null && expiresAt <= now` → `'expired'`; `maxClicks !== null && clickCount >= maxClicks` → `'exhausted'`; senão `'active'`.

### 5.2 Portas (`ports.ts`)

```ts
export interface Clock { now(): Date }

export type ThreatVerdict = 'safe' | 'dangerous' | 'unavailable'
export interface UrlThreatChecker { check(url: string): Promise<ThreatVerdict> }

export interface LinkRepository {
  insert(link: NewLink): Promise<{ status: 'created'; id: number } | { status: 'slug-taken' }>
  consumeClick(slug: string, now: Date): Promise<{ id: number; destinationUrl: string } | null>
  findBySlug(slug: string): Promise<LinkSnapshot | null>
  findByTokenHash(hash: Uint8Array): Promise<LinkSnapshot | null>
  deactivateByTokenHash(hash: Uint8Array, now: Date): Promise<'deactivated' | 'unchanged'>
}

export interface ClickEventRepository {
  record(event: { linkId: number; deviceType: DeviceType; referrerHost: string | null }): Promise<void>
  getStats(linkId: number, dailyFrom: Date): Promise<RawClickStats>
}
```

`RawClickStats` = `{ byDevice: Partial<Record<DeviceType, number>>; byReferrer: { host: string | null; count: number }[]; daily: { day: string; count: number }[] }` (`byReferrer` e `daily` já sem `BOT`; `byDevice` inclui `BOT`).

O `UrlThreatChecker` devolve `'unavailable'` em vez de lançar: o fail-closed (B1) fica explícito no tipo, sem `catch`.

### 5.3 Formatos (`slug.ts`, `manage-token.ts`)

| Função | Regra | Como |
|---|---|---|
| `isValidSlugFormat(s)` | 7 caracteres base62 | `/^[A-Za-z0-9]{7}$/` |
| `generateSlug()` | CSPRNG, sem viés | `crypto.getRandomValues` em lotes; aceita o byte só se `< 248` (4 × 62) e usa `byte % 62` (amostragem por rejeição) |
| `isValidManageTokenFormat(t)` | 43 caracteres base64url | `/^[A-Za-z0-9_-]{43}$/` |
| `generateManageToken()` | 32 bytes de CSPRNG, base64url sem padding | `btoa` sobre os bytes, troca `+`→`-`, `/`→`_`, remove `=` |
| `hashManageToken(t)` | SHA-256 | `crypto.subtle.digest('SHA-256', new TextEncoder().encode(t))` → `Uint8Array` (32 bytes) |

O hash é calculado sobre os 43 caracteres ASCII do token, sem decodificar o base64url.

### 5.4 Tempo em `America/Sao_Paulo` (`sao-paulo-time.ts`)

Regras: `link-lifecycle.md` ("Relógio", "Expiração"), `data-model.md` ("dia" das estatísticas). Sem biblioteca; o Node 24 não tem `Temporal`.

```ts
export function todayInSaoPaulo(now: Date): string                // 'YYYY-MM-DD'
export function saoPauloOffset(date: string, time: string): string // ex.: '-03:00'
export function endOfDayInSaoPaulo(date: string): Date             // 23:59:59.999 local
export function startOfDayInSaoPaulo(date: string): Date           // 00:00:00.000 local
export function addDays(date: string, days: number): string
```

- `todayInSaoPaulo`: `Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(now)`.
- `saoPauloOffset`: `Intl.DateTimeFormat('en-US', { timeZone: 'America/Sao_Paulo', timeZoneName: 'longOffset' })` sobre o instante aproximado (`<date>T<time>-03:00`), lendo a parte `timeZoneName` (`GMT-03:00` → `-03:00`; `GMT` puro → `+00:00`). Respeita a base IANA: dezembro de 2018 devolve `-02:00` (horário de verão).
- `endOfDayInSaoPaulo('2026-10-30')` → `new Date('2026-10-30T23:59:59.999-03:00')`.
- Os rascunhos de SQL com `now()` usam o parâmetro do `Clock` (B-1); só `created_at` e `clicked_at` usam o `now()` do banco como padrão.

### 5.5 `UrlValidator` (`url-validator.ts`)

Regras: `url-validation.md` (R1 a R6, IDN, P6, RC2, RC10, B-2).

```ts
export type UrlViolation =
  | 'invalid' | 'protocol' | 'credentials' | 'own-domain'
  | 'not-public' | 'ipv6-literal' | 'too-long'

export class UrlValidator {
  constructor(private readonly ownHosts: readonly string[]) {}
  validate(input: string):
    | { ok: true; href: string; isInsecure: boolean }
    | { ok: false; violation: UrlViolation }
}
```

Algoritmo (a entrada já chega com `trim()` e com no máximo 2048 caracteres):

1. `new URL(input)`. Se lançar, **R6**: `new URL('https://' + input)`. Se lançar de novo → `'invalid'`. Consequência documentada: `localhost:3000` e `site.com:8080/x` são lidos como protocolo e caem na R1 (o usuário digita o `https://`).
2. **R1:** `protocol` fora de `http:`/`https:` → `'protocol'`.
3. **R2:** `username` ou `password` não vazios → `'credentials'`.
4. **R4:** sobre `hostname` (já em minúsculas e em punycode pelo parser WHATWG, que também normaliza IPv4 em octal, hexadecimal ou com menos de 4 partes), **sem um ponto final** (o parser mantém `localhost.` e `site.com.`, que o DNS trata como o mesmo nome; medido no Node 24; vale também para a R3):
   - começa com `[` → `'ipv6-literal'` (RC10);
   - `localhost` ou termina em `.localhost` (RFC 6761), `.local` (RFC 6762), `.home.arpa` (RFC 8375) ou `.internal` (reservado pela ICANN em 2024) → `'not-public'`;
   - sem ponto (`intranet`) → `'not-public'`;
   - IPv4 em faixa não pública do registro IANA de endereços de uso especial (RFC 6890): `0/8`, `10/8`, `100.64/10`, `127/8`, `169.254/16`, `172.16/12`, `192.0.0/24`, `192.0.2/24`, `192.168/16`, `198.18/15`, `198.51.100/24`, `203.0.113/24`, `224/4`, `240/4` → `'not-public'`.
5. **R3:** `hostname` sem o ponto final igual a algum dos `ownHosts` → `'own-domain'`.
6. **R5:** `url.href.length > 2048` → `'too-long'`.
7. Sucesso: `href = url.href` (B-2: o mesmo texto é gravado, enviado à R7 e usado no `Location`) e `isInsecure = protocol === 'http:'`.

Uma violação por campo: vale a primeira, na ordem acima.

### 5.6 Clique: dispositivo, referrer e bots (`click-tracker.ts`, `preview-bot.ts`)

Regras: `data-model.md` (dispositivo e referrer), `redirect.md` ("Bots de preview", B-3).

```ts
export function isPreviewBot(userAgent: string | null): boolean
export function classifyDevice(h: { userAgent: string | null; secChUaMobile: string | null }): Exclude<DeviceType, 'BOT'>
export function extractReferrerHost(referer: string | null): string | null
```

- `isPreviewBot`: lista fixa, cada padrão na forma mais específica documentada (B-3): `/^WhatsApp\//`, `/^Slackbot/`, `/^facebookexternalhit\//`, `/^Twitterbot\//`, `/^TelegramBot/`, `/^LinkedInBot\//`, `/Discordbot\//`. **A lista exata de padrões é conferida na documentação de cada plataforma na tarefa**, e o teste inclui UAs reais dos navegadores embutidos do Facebook (`FBAN`/`FBAV`) e do Instagram, que devem continuar humanos.
- `classifyDevice`: sem UA (ausente ou `''`) → `'UNKNOWN'`; `secChUaMobile === '?1'` → `'MOBILE'`; `/iPad|Tablet/i` → `'TABLET'`; `/Mobi|Android|iPhone/i` → `'MOBILE'`; senão `'DESKTOP'`.
- `extractReferrerHost`: `new URL(referer)` dentro de `try`; só `http:`/`https:`; `hostname` em minúsculas, sem um `www.` no início; host vazio depois disso (`https://www./`) ou qualquer falha → `null`.

### 5.7 `LinkService` (`link-service.ts`)

```ts
export interface CreateLinkInput {
  destination: string            // já com trim(), não vazia, ≤ 2048
  maxClicks: number | null       // já inteiro (rodada de formato)
  expiration: ExpirationChoice
}

export type CreateLinkFieldError =
  | { field: 'url'; code: UrlViolation }
  | { field: 'maxClicks'; code: 'out-of-range' }
  | { field: 'expiration'; code: 'past-date' | 'too-far' }

export type CreateLinkResult =
  | { status: 'created'; slug: string; manageToken: string; isInsecureDestination: boolean }
  | { status: 'invalid'; errors: CreateLinkFieldError[] }
  | { status: 'threat' }
  | { status: 'unavailable'; cause: 'threat-checker' | 'slug-collisions' }

export class LinkService {
  constructor(deps: {
    links: LinkRepository
    clickEvents: ClickEventRepository
    threatChecker: UrlThreatChecker
    urlValidator: UrlValidator
    clock: Clock
  })
  create(input: CreateLinkInput): Promise<CreateLinkResult>
  getManagementView(manageToken: string): Promise<ManagementView | null>
  deactivate(manageToken: string): Promise<'deactivated' | 'already-deactivated' | 'not-found'>
}
```

**`create`** (segunda rodada da RC7, `link-creation.md` "Fluxo"):

1. Junta os erros de regra de **todos** os campos: `urlValidator.validate`; `maxClicks` fora de 1 a 1.000.000; data do `end-of-day` antes de `todayInSaoPaulo(now)` (`'past-date'`) ou depois de hoje + 5 anos (`'too-far'`; comparação de strings `YYYY-MM-DD`, com o ano somado). Algum erro → `{ status: 'invalid' }`, **sem** consultar o Google.
2. **R7:** `threatChecker.check(href)`: `'dangerous'` → `{ status: 'threat' }`; `'unavailable'` → `{ status: 'unavailable', cause: 'threat-checker' }`.
3. `expiresAt`: `none` → `null`; `duration` → `now + EXPIRATION_DURATION_MS`; `end-of-day` → `endOfDayInSaoPaulo(date)`.
4. Gera o token e o hash uma vez; gera o slug e chama `links.insert`, até **3 tentativas** enquanto vier `'slug-taken'`. Esgotou → `{ status: 'unavailable', cause: 'slug-collisions' }` (a entrada loga como erro).
5. Erro do repositório (banco fora) **propaga**; a entrada traduz (§8.3).

**`getManagementView`**: formato inválido → `null`; hash → `links.findByTokenHash` → `null` se não existir. Senão monta:

```ts
export interface ManagementView {
  slug: string
  destinationUrl: string
  state: 'active' | GoneReason
  clickCount: number
  maxClicks: number | null
  expiresAt: Date | null
  deactivatedAt: Date | null
  createdAt: Date
  stats: ClickStats // §5.9
}
```

**`deactivate`**: formato inválido → `'not-found'`; `links.deactivateByTokenHash(hash, now)`: `'deactivated'` → `'deactivated'`; `'unchanged'` → `findByTokenHash`: `null` → `'not-found'`, senão `'already-deactivated'` (idempotente, mantém a data original; `manage-page.md`). O link é sempre identificado pelo hash do token, nunca pelo slug (IDOR).

### 5.8 `RedirectService` (`redirect-service.ts`)

Regras: `redirect.md` ("Fluxo", "Bots de preview", "Requisições `HEAD`", RC9).

```ts
export type RedirectMode = 'visit' | 'peek' // peek = HEAD ou bot de preview

export type RedirectOutcome =
  | { kind: 'redirect'; linkId: number; destinationUrl: string }
  | { kind: 'limited-preview'; linkId: number } // página neutra, sem revelar o destino
  | { kind: 'not-found' }
  | { kind: 'gone'; reason: GoneReason }

export class RedirectService {
  constructor(deps: { links: LinkRepository; clock: Clock })
  resolve(slug: string, mode: RedirectMode): Promise<RedirectOutcome>
}
```

- `visit`: `links.consumeClick(slug, now)`. Uma linha → `redirect`. Vazio → `findBySlug`: `null` → `not-found`; senão `classifyLink` → `gone`. Se `classifyLink` disser `'active'` depois do UPDATE vazio, é violação de invariante (o contador só sobe, a desativação é irreversível, a expiração é fixa): lança erro, que vira `503` e log `unexpected-error`.
- `peek`: só `findBySlug`. `null` → `not-found`; inativo → `gone`; `maxClicks === null` → `redirect` (sem incrementar); senão → `limited-preview`.
- O formato do slug é checado **antes**, na entrada (o `404` sai sem rate limit e sem banco).

### 5.9 Estatísticas (`click-stats.ts`)

Regras: `manage-page.md` (janela, RC8, RC9, S5).

```ts
export interface ClickStats {
  humanTotal: number                    // soma dos eventos humanos
  botPreviews: number                   // eventos BOT, toda a vida
  byDevice: { device: Exclude<DeviceType, 'BOT'>; count: number }[]
  topReferrers: { host: string | null; count: number }[] // até 10, desc.
  otherReferrers: number                // soma do que passar dos 10
  daily: { day: string; count: number }[] // janela completa, dias sem clique = 0
  detailBelowTotal: boolean             // humanTotal < clickCount → mostra a nota da RC8
}
export function dailyWindow(createdAt: Date, now: Date): { fromDay: string; toDay: string }
export function buildClickStats(raw: RawClickStats, clickCount: number, window: { fromDay: string; toDay: string }): ClickStats
```

- `dailyWindow`: `toDay = todayInSaoPaulo(now)`; `fromDay = min(toDay, max(addDays(toDay, -29), todayInSaoPaulo(createdAt)))` (30 dias, ou desde a criação). O `min` cobre o `created_at` gravado pelo relógio do banco alguns milissegundos à frente do relógio da função na virada do dia (B-1): a janela nunca fica invertida.
- `byDevice` sem os dispositivos com zero, em ordem decrescente de contagem (empate: `MOBILE`, `DESKTOP`, `TABLET`, `UNKNOWN`). `topReferrers` em ordem decrescente (empate: host em ordem alfabética, `null` por último). Saída determinística para o teste e para a tela.
- O `getManagementView` chama `clickEvents.getStats(id, startOfDayInSaoPaulo(fromDay))` e passa o resultado a `buildClickStats`, que completa os dias vazios com zero.
- **Referrers: os 10 maiores, e o resto somado em "outros".** Detalhe desta spec, não decisão de regra: limita a tela contra *referral spam* sem mudar o banco.

## 6. Dados (`src/data/`)

Regras: `.agents/context/data-model.md`, `.agents/rules/architecture-persistence.md`.

### 6.1 Schema (`prisma/schema.prisma`)

```prisma
generator client {
  provider = "prisma-client"
  output   = "../src/data/generated/prisma"
}

datasource db {
  provider = "postgresql"
}

enum DeviceType {
  MOBILE
  DESKTOP
  TABLET
  BOT
  UNKNOWN
}

model Link {
  id              Int          @id @default(autoincrement())
  slug            String       @unique
  destinationUrl  String       @map("destination_url")
  manageTokenHash Bytes        @unique @map("manage_token_hash")
  clickCount      Int          @default(0) @map("click_count")
  maxClicks       Int?         @map("max_clicks")
  expiresAt       DateTime?    @map("expires_at") @db.Timestamptz(3)
  deactivatedAt   DateTime?    @map("deactivated_at") @db.Timestamptz(3)
  createdAt       DateTime     @default(now()) @map("created_at") @db.Timestamptz(3)
  clickEvents     ClickEvent[]

  @@map("links")
}

model ClickEvent {
  id           BigInt     @id @default(autoincrement())
  linkId       Int        @map("link_id")
  link         Link       @relation(fields: [linkId], references: [id], onDelete: Restrict)
  deviceType   DeviceType @map("device_type")
  referrerHost String?    @map("referrer_host")
  clickedAt    DateTime   @default(now()) @map("clicked_at") @db.Timestamptz(3)

  @@index([linkId, clickedAt])
  @@map("click_events")
}
```

A URL do banco não fica no schema: no Prisma 7, ela vai para o `prisma.config.ts` (§9.5). A primeira migration é gerada com `prisma migrate dev --name init` e conferida à mão (tipos `timestamptz(3)`, `bytea`, `UNIQUE`, índice composto, FK `RESTRICT`).

### 6.2 Client e pool (`prisma-client.ts`)

```ts
import { Pool } from 'pg'
import { attachDatabasePool } from '@vercel/functions'
import { PrismaPg } from '@prisma/adapter-pg'
import { PrismaClient } from './generated/prisma/client' // caminho exato conferido no generate

export function createPrismaClient(options: {
  connectionString: string
  max?: number                       // teste de concorrência: 20
  connectionTimeoutMillis?: number   // padrão 5000; o teste de timeout usa menos
  logQueries?: boolean               // teste do UPDATE atômico (uma instrução só)
}): { prisma: PrismaClient; pool: Pool }

let prisma: PrismaClient | undefined
export function getPrismaClient(): PrismaClient // cria na primeira chamada
```

`createPrismaClient`: `new Pool({ connectionString, max, idleTimeoutMillis: 5000, connectionTimeoutMillis: 5000 })` e `new PrismaClient({ adapter: new PrismaPg(pool) })`. Os testes de integração criam os próprios clientes com ela e encerram com `pool.end()` (o `$disconnect()` não fecha um pool externo; conferir na tarefa).

`getPrismaClient`, na primeira chamada: `createPrismaClient({ connectionString: process.env.DATABASE_URL })` e `attachDatabasePool(pool)`. `DATABASE_URL` ausente → erro explícito que cita o nome da variável, nunca uma URL (fail-fast). Singleton no escopo do módulo, também no `next dev` (guardado em `globalThis` para sobreviver ao recarregamento). Os repositórios recebem o `PrismaClient` pelo construtor.

### 6.3 `PrismaLinkRepository` (`prisma-link-repository.ts`)

**`insert`:** `link.create`; erro `P2002` no `slug` → `{ status: 'slug-taken' }` (detectado na gravação, nunca "consultar e depois gravar"). `P2002` em `manage_token_hash` (probabilidade desprezível) propaga como erro inesperado.

**`consumeClick` — UPDATE atômico** (forma de referência; `$2` é o `Clock`, B-1):

```sql
UPDATE links
SET click_count = click_count + 1
WHERE slug = $1
  AND deactivated_at IS NULL
  AND (max_clicks IS NULL OR click_count < max_clicks)
  AND (expires_at IS NULL OR expires_at > $2)
RETURNING id, destination_url;
```

Implementação com o Prisma, sem SQL cru (`updateManyAndReturn` existe desde a 6.2.0 para PostgreSQL; a comparação entre colunas usa a propriedade `.fields`):

```ts
const rows = await prisma.link.updateManyAndReturn({
  where: {
    slug,
    deactivatedAt: null,
    AND: [
      { OR: [{ maxClicks: null }, { clickCount: { lt: prisma.link.fields.maxClicks } }] },
      { OR: [{ expiresAt: null }, { expiresAt: { gt: now } }] },
    ],
  },
  data: { clickCount: { increment: 1 } },
  select: { id: true, destinationUrl: true }, // (conferir na tarefa)
})
```

**Conferir na tarefa, com o log de queries do Prisma ligado no teste de integração, que sai um único `UPDATE … RETURNING`.** O teste de concorrência (§11) é a prova. Se o Prisma dividir em duas instruções, o método passa para `$queryRaw` com o SQL acima (permitido pela RC3, só em `src/data/`). Nota: o Prisma 8 renomeia o método para `updateAll()`; o projeto fixa o 7.10.0.

**`findBySlug` / `findByTokenHash`:** `findUnique` pela coluna `UNIQUE`, mapeando para `LinkSnapshot`.

**`deactivateByTokenHash`** (forma de referência):

```sql
UPDATE links SET deactivated_at = $2
WHERE manage_token_hash = $1 AND deactivated_at IS NULL;
```

Via `link.updateMany`; `count === 1` → `'deactivated'`, `0` → `'unchanged'`.

### 6.4 `PrismaClickEventRepository` (`prisma-click-event-repository.ts`)

- **`record`:** `clickEvent.create` (o `clicked_at` vem do `now()` do banco).
- **`getStats`:** três consultas em `Promise.all`:
  - dispositivos: `clickEvent.groupBy({ by: ['deviceType'], where: { linkId }, _count: { _all: true } })`;
  - referrers: `clickEvent.groupBy({ by: ['referrerHost'], where: { linkId, deviceType: { not: 'BOT' } }, _count: { _all: true } })`; o domínio ordena por contagem e corta em 10 (o grupo `null`, "direto ou desconhecido", disputa como qualquer outro);
  - gráfico diário (RC3, único SQL cru do projeto, em template marcado):

```ts
const rows = await prisma.$queryRaw<{ day: string; count: bigint }[]>`
  SELECT to_char(date_trunc('day', clicked_at AT TIME ZONE 'America/Sao_Paulo'), 'YYYY-MM-DD') AS day,
         count(*) AS count
  FROM click_events
  WHERE link_id = ${linkId}
    AND device_type <> 'BOT'
    AND clicked_at >= ${dailyFrom}
  GROUP BY 1
  ORDER BY 1`
// count chega como bigint e é convertido com Number() (no máximo 1 milhão por link no MVP)
```

O tipo do resultado é declarado à mão e conferido pelo teste contra o Postgres do Docker. O índice `(link_id, clicked_at)` cobre as três consultas.

### 6.5 Erros do banco (`database-errors.ts`)

```ts
export function isDatabaseUnavailableError(error: unknown): boolean
export function withDatabaseErrors<T>(operation: () => Promise<T>): Promise<T> // traduz e relança
```

O domínio define `RepositoryUnavailableError` (`errors.ts`, com `cause`). Cada método dos repositórios passa por `withDatabaseErrors`, que traduz para ele os erros de conectividade: timeout de conexão do `pg`, `ECONNREFUSED`, `ETIMEDOUT`, `ENOTFOUND` e os códigos do Prisma `P1001`, `P1002` e `P2024`. **A lista exata é conferida na tarefa, derrubando o Postgres do Docker e lendo o erro real.** Os testes simulam os dois casos sem derrubar o container: cliente para uma porta fechada (`127.0.0.1:1`, recusa) e um servidor TCP local mudo (timeout). Qualquer outro erro propaga como inesperado, inclusive o `P2002`.

## 7. Integrações externas (`src/infra/`)

Regras: `.agents/rules/security-blocklist.md` (B1 a B3, S3, S4), `.agents/context/url-validation.md` (R7), `.agents/rules/architecture-local-dev.md`.

### 7.1 `SafeBrowsingUrlThreatChecker`

```ts
export class SafeBrowsingUrlThreatChecker implements UrlThreatChecker {
  constructor(deps: { apiKey: string; fetch?: typeof fetch; now?: () => number; maxCacheEntries?: number })
  check(url: string): Promise<ThreatVerdict>
}
```

**Expressões (`safe-browsing-expressions.ts`, funções puras):** `canonicalize(href)` e `buildExpressions(canonical)`, seguindo a doc "URLs and Hashing" da v5:

1. Remove tab, CR e LF; remove o fragmento; desfaz o *percent-encoding* repetidamente até não sobrar escape.
2. Host: remove pontos no início e no fim, junta pontos repetidos, minúsculas. IPv4 já chega normalizado pelo `new URL()`; IPv6 nunca chega (R4).
3. Caminho: resolve `/./` e `/../`, junta barras repetidas (não mexe na query).
4. Refaz o escape de todo caractere `<= 0x20`, `>= 0x7F`, `#` e `%`, com hexadecimal maiúsculo.
5. **Hosts (S3, regra da v4):** o host exato mais até 4 hosts formados pelos últimos 5 pedaços, tirando um da frente por vez e pulando o TLD sozinho; nada disso para IP.
6. **Caminhos:** o caminho exato com a query, o caminho exato sem a query e até 4 prefixos a partir de `/`, com barra no fim.
7. Combinações host × caminho, sem repetição, no máximo 30.

**Consulta:** SHA-256 de cada expressão (`crypto.subtle`), prefixo de 4 bytes em base64 padrão. Prefixos com entrada válida no cache (S4) não vão à rede. Os restantes vão numa chamada só:

```
GET https://safebrowsing.googleapis.com/v5/hashes:search?key=<API_KEY>&hashPrefixes=<b64>&hashPrefixes=<b64>…
```

com `signal: AbortSignal.timeout(2000)`. A URL montada **nunca** é logada (leva a chave).

**Resposta:** `{ fullHashes?: { fullHash: string; fullHashDetails?: { threatType: string; attributes?: string[] }[] }[]; cacheDuration: string }`.

- Um `fullHashDetail` só conta se o `threatType` for conhecido (`MALWARE`, `SOCIAL_ENGINEERING`, `UNWANTED_SOFTWARE`, `POTENTIALLY_HARMFUL_APPLICATION`) e se não tiver os atributos `CANARY` ("should not be used for enforcement") nem `FRAME_ONLY` (só vale para *frames*, e o redirect é navegação de topo). Valor desconhecido → descarta o detalhe inteiro, como a referência exige.
- `'dangerous'` se algum hash completo com detalhe válido for igual ao hash de alguma expressão.
- **Cache (S4):** `Map<prefixo, { expiresAt: number; fullHashes: Set<string> }>`, com `expiresAt = now() + cacheDuration` (formato `"300s"` ou `"3.5s"`), **nunca estendido**, gravado para todo prefixo consultado, inclusive os sem resultado. Teto `maxCacheEntries` (padrão 5.000): passando dele, remove as entradas mais antigas (ordem de inserção do `Map`).
- **Falhas → `'unavailable'` (B1, fail-closed):** timeout, erro de rede, status diferente de 200 (inclusive `429` de cota) ou JSON fora do formato. É o **desvio consciente** do procedimento do Google, que devolve "seguro" na falha.

### 7.2 `LocalFakeUrlThreatChecker`

`'dangerous'` só para `https://testsafebrowsing.appspot.com/s/phishing.html` e `…/s/malware.html` (comparação com o `href` normalizado); `'safe'` para o resto. Sem rede. Usado só com a trava 1 (§4.3).

### 7.3 `UnavailableUrlThreatChecker`

Devolve `'unavailable'` na hora, sem rede (RC4). Injetado quando a `SAFE_BROWSING_API_KEY` falta.

## 8. Entrada (`src/app/`)

### 8.1 Origem canônica (`app-origin.ts`)

Regras: `url-validation.md` (R3, RC2).

```ts
export interface AppOrigin { origin: string; ownHosts: string[] }
export function resolveAppOrigin(env: Record<string, string | undefined>): AppOrigin | null
```

1. `APP_ORIGIN` definida: `new URL()`, só `http:`/`https:`, sem caminho além de `/` → `origin = url.origin`.
2. Senão, `VERCEL_ENV === 'production'` → `https://` + `VERCEL_PROJECT_PRODUCTION_URL`; `VERCEL_ENV === 'preview'` → `https://` + `VERCEL_BRANCH_URL`.
3. Nada disso → `null`, e quem chamou trata como erro de configuração (`app-origin-missing`, log de erro).

`ownHosts` = host da origem + host de `VERCEL_PROJECT_PRODUCTION_URL` (quando existir), sem repetição. O redirect não chama esta função.

### 8.2 Rate limit (`rate-limit.ts`, `client-ip.ts`)

Regras: `.agents/rules/security-rate-limit.md` (10a a 10d, RC4, RC5).

```ts
export const RATE_LIMITS = {
  createPerMinute: { requests: 10, window: '1 m' },
  createPerDay: { requests: 100, window: '24 h' },
  redirectPerMinute: { requests: 300, window: '1 m' },
  timeoutMs: 1000,
} as const

export type RateLimitDecision =
  | { outcome: 'allowed' }
  | { outcome: 'limited'; scope: 'minute' | 'day'; retryAfterSeconds: number }
  | { outcome: 'unavailable' }

export interface RateLimiter {
  checkCreation(key: string): Promise<RateLimitDecision> // minuto e depois dia
  checkRedirect(key: string): Promise<RateLimitDecision>
}
```

- **`UpstashRateLimiter`:** recebe os três limitadores pelo construtor, para o teste usar falsos: `constructor(deps: { createPerMinute: Limiter; createPerDay: Limiter; redirectPerMinute: Limiter; now?: () => number })`, com `type Limiter = { limit(key: string): Promise<{ success: boolean; reset: number; reason?: string }> }`. `limit(key)`: `success` → segue; `!success` → `limited` com `retryAfterSeconds = ceil((reset − agora) / 1000)`; `reason === 'timeout'` ou exceção → `unavailable`, com log `rate-limiter-unavailable` (sem a chave). Na criação, a checagem diária só roda se a do minuto passou.
- **`createUpstashRateLimiter(env: { url: string; token: string; vercelEnv: string | undefined })`** monta os reais: três `new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(n, janela), prefix, timeout: 1000, analytics: false })`, com `redis = new Redis({ url, token })` de `@upstash/redis` e `prefix = rateLimitPrefix(vercelEnv, scope)`. **(conferir na tarefa no código publicado de `@upstash/ratelimit`, como na RC4.)**
- **`rateLimitPrefix(vercelEnv: string | undefined, scope: 'create-min' | 'create-day' | 'redirect'): string`** → `short-url:<VERCEL_ENV ou local>:<scope>` (previews separados da produção).
- **`InMemoryRateLimiter`:** `constructor(deps?: { now?: () => number })`; janelas deslizantes com os mesmos números, num `Map` por instância (só `npm run dev`).
- **`UnavailableRateLimiter`:** sempre `unavailable`.
- **Chave (`client-ip.ts`):** `rateLimitKey(ip: string | undefined, nodeEnv: string | undefined): string | null`. `nodeEnv === 'development'` → `'local-dev'`. `ip` ausente → `null`. IPv4 com 4 partes decimais válidas → ele mesmo. IPv4 mapeado (`::ffff:a.b.c.d`) → o IPv4. IPv6 → expande o `::`, minúsculas, 4 primeiros grupos com 4 dígitos + `::/64`. Qualquer outra coisa → `null`. `null` vale como `unavailable` (RC5).
- **O IP vem de** `ipAddress(request)` no redirect e `ipAddress(await headers())` na action (`@vercel/functions`, lê o `x-real-ip`).

### 8.3 Criação

Regras: `link-creation.md`, `error-map.md`, `link-lifecycle.md`, `url-validation.md`.

**Campos do formulário:** `url`, `maxClicks`, `expirationDuration` (`1h`, `24h`, `7d` ou `30d`) e `expirationDate` (`YYYY-MM-DD`). Na tela, um grupo de `<input type="radio">` nativo escolhe "sem expiração", "duração" ou "até o fim do dia"; o campo da opção não escolhida fica `disabled` e não é enviado.

**Rodada de formato (`create-link-form.ts`, RC7):**

```ts
export function parseCreateLinkForm(form: FormData):
  | { ok: true; input: CreateLinkInput }
  | { ok: false; errors: FormFieldError[] }
```

```ts
export type FormFieldError =
  | { field: 'url'; code: 'required' | 'too-long' }
  | { field: 'maxClicks'; code: 'not-integer' }
  | { field: 'expiration'; code: 'both' | 'invalid-duration' | 'invalid-date' }
```

`trim()` em todos os campos (P4). Campo ausente vale como vazio; campo que chega como `File` (requisição forjada) também vale como vazio no `url` e como `'not-integer'` no `maxClicks`, sem exceção; campo repetido usa o primeiro (`form.get`). `url`: vazio → `'required'`; mais de 2048 → `'too-long'`. `maxClicks`: vazio → `null`; fora de `/^\d+$/` → `'not-integer'`; senão `Number()`. Expiração: os dois campos preenchidos → `'both'`; duração fora da lista → `'invalid-duration'`; data fora de `/^\d{4}-\d{2}-\d{2}$/` ou que não sobrevive a `Date.UTC` ida e volta (`2026-02-30`) → `'invalid-date'`; nenhum → `{ kind: 'none' }`. Junta os erros de todos os campos, um por campo, na ordem `url`, `maxClicks`, `expiration`.

**Estado (`create-link-state.ts`):**

```ts
export type CreateLinkState =
  | { status: 'idle' }
  | {
      status: 'success'
      shortUrl: string
      manageUrl: string
      qrCodeDataUrl: string | null // null = QR falhou (P1)
      isInsecureDestination: boolean
    }
  | {
      status: 'error'
      fieldErrors?: Partial<Record<'url' | 'maxClicks' | 'expiration', string>>
      message?: string
      threatAdvisory?: true // desenha a linha "Advisory provided by Google" (B3)
    }
```

As mensagens saem de uma função que segue o `error-map.md` à risca; o domínio só devolve códigos:

```ts
export type CreateLinkFailure =
  | { kind: 'form'; errors: FormFieldError[] }
  | { kind: 'domain'; result: Exclude<CreateLinkResult, { status: 'created' }> }
  | { kind: 'rate-limited'; scope: 'minute' | 'day' }
  | { kind: 'unavailable' }
  | { kind: 'unexpected' }
export function toCreateLinkErrorState(failure: CreateLinkFailure): Extract<CreateLinkState, { status: 'error' }>
```

**Server Action (`actions/create-link.ts`):**

```ts
'use server'
export async function createLink(prev: CreateLinkState, form: FormData): Promise<CreateLinkState>

// src/app/_lib/create-link-handler.ts: a action só monta as dependências reais e chama
export function handleCreateLink(form: FormData, deps: {
  ip: string | undefined                 // ipAddress(await headers())
  nodeEnv: string | undefined
  env: Record<string, string | undefined> // para o resolveAppOrigin
  rateLimiter: RateLimiter
  linkService: Pick<LinkService, 'create'>
  generateQrCode: (url: string) => Promise<string>
}): Promise<CreateLinkState>
```

Passos do `handleCreateLink`:

1. `rateLimitKey(ipAddress(await headers()), NODE_ENV)` → `getRateLimiter().checkCreation(key)`: `limited` → mensagem do minuto ou do dia; `unavailable` (ou chave `null`) → "Não foi possível criar o link agora…" + log.
2. `resolveAppOrigin(process.env)`: `null` → a mesma mensagem + log de erro (RC2, fail-fast).
3. `parseCreateLinkForm` → erros → estado `error`.
4. `getLinkService().create(input)` → `invalid` / `threat` / `unavailable` → estado `error` (colisões e Google com log). `RepositoryUnavailableError` → "Não foi possível criar o link agora…" + log; outro erro → "Algo deu errado. Tente novamente." + log `unexpected-error`.
5. `created` → `shortUrl = origin + '/' + slug`, `manageUrl = origin + '/manage/' + token`; `qrCodeDataUrl = await generateQrCodeDataUrl(shortUrl)` dentro de `try` (falhou → `null` + log `qr-failed`, P1). Devolve `success`.

**QR (`qr-code.ts`):** `QRCode.toDataURL(shortUrl, { width: 512, margin: 2, errorCorrectionLevel: 'M' })` da `qrcode@1.5.4`. A mesma função serve a gestão.

**Tela:** `create-link-form.tsx` usa `useActionState(createLink, { status: 'idle' })`; botão desabilitado com "Encurtando…" enquanto `isPending` (P3). `expiration-field.tsx` mostra "Expira em DD/MM/AAAA às 23:59 (horário de Brasília)" ou "Expira **hoje** às 23:59 (horário de Brasília)", calculado no navegador por `formatExpirationLabel(date: string, now: Date): { kind: 'today' } | { kind: 'date'; formatted: string }` (`src/components/expiration-label.ts`, puro, usa `todayInSaoPaulo`) (P7). `link-result-card.tsx`: link de gestão em destaque acima do link curto, com o aviso "guarde este link: não há recuperação" (P5-C); `beforeunload` ligado até o primeiro "copiar" do link de gestão (P5-B); botões "copiar" (`navigator.clipboard.writeText`) e "baixar QR" (`<a href={qrCodeDataUrl} download="qr-<slug>.png">`); aviso de destino `http:` quando `isInsecureDestination`; "Não foi possível gerar o QR code" quando `qrCodeDataUrl === null`. Nada do token vai para `localStorage`, cookie ou log.

### 8.4 Redirect (`[slug]/route.ts`, `redirect-handler.ts`)

Regras: `redirect.md`, `security-rate-limit.md`.

```ts
// src/app/[slug]/route.ts
export async function GET(request: Request, ctx: { params: Promise<{ slug: string }> }): Promise<Response>
export async function HEAD(request: Request, ctx: { params: Promise<{ slug: string }> }): Promise<Response>
// os dois chamam handleRedirect com as dependências reais (scheduleAfter: after)

// src/app/_lib/redirect-handler.ts
export function handleRedirect(request: Request, slug: string, method: 'GET' | 'HEAD', deps: {
  redirectService: RedirectService
  clickEvents: ClickEventRepository
  rateLimiter: RateLimiter
  scheduleAfter: (task: () => Promise<void>) => void
  nodeEnv: string | undefined
}): Promise<Response>
```

O `HEAD` próprio é obrigatório: sem ele, o Next 16 responde o `HEAD` executando o `GET` e consome o link. **`handleRedirect`:**

```
1. !isValidSlugFormat(slug)                 → 404 (sem Upstash nem banco)
2. key = rateLimitKey(ipAddress(request), NODE_ENV)
   key !== null → checkRedirect(key): limited → 429 + Retry-After; unavailable → segue (fail-open)
   key === null → segue (fail-open) + log
3. isBot = isPreviewBot(user-agent); mode = (HEAD || isBot) ? 'peek' : 'visit'
4. outcome = getRedirectService().resolve(slug, mode)
     redirect        → 302, Location = destinationUrl, Cache-Control: no-store
     limited-preview → 200, página neutra (§8.6)
     not-found       → 404 · gone → 410 com o motivo
5. after(): grava evento só se outcome ∈ {redirect, limited-preview} e o método for GET
     bot → BOT · humano → classifyDevice(user-agent, sec-ch-ua-mobile) + extractReferrerHost(referer)
     (os headers são lidos e classificados antes do after(); o callback só grava)
6. qualquer exceção do passo 4 → 503 + Retry-After: 30, log com o slug (nunca o destino)
```

- O `Location` é o `href` gravado (B-2), já em ASCII (punycode e *percent-encoding*), portanto válido como header. A query do link curto é ignorada (P2).
- O `302` é montado com `new Response(null, { status: 302, headers })`.
- `HEAD` responde com o mesmo status e os mesmos headers, sem corpo, e nunca grava evento.
- O callback do `after()` captura o próprio erro e loga `click-event-failed` com o slug.
- `GET` de Route Handler não é cacheado por padrão desde o Next 15, e a rota lê `request`, então é dinâmica.

### 8.5 Gestão (`manage/[token]/page.tsx`, `actions/deactivate-link.ts`)

Regras: `manage-page.md`, `security-token.md`, `error-map.md`.

**Página (Server Component, dinâmica):** a `page.tsx` chama o *loader* e só renderiza o resultado:

```ts
// src/app/_lib/manage-page-loader.ts
export function loadManagementPage(token: string, deps: {
  linkService: Pick<LinkService, 'getManagementView'>
  env: Record<string, string | undefined>
  generateQrCode: (url: string) => Promise<string>
}): Promise<
  | { kind: 'not-found' }                 // → notFound()
  | { kind: 'unavailable' }               // → tela "Serviço indisponível…"
  | { kind: 'ok'; view: ManagementView; shortUrl: string; qrCodeDataUrl: string | null }
>
// erro inesperado propaga (a página de erro do Next responde 500)
```

1. `token` fora do formato → `notFound()` (sem banco).
2. `getLinkService().getManagementView(token)`: `null` → `notFound()` (a mesma página para "não existe" e "fora do formato"). `RepositoryUnavailableError` → renderiza "Serviço indisponível. Tente novamente em instantes." (limitação: HTTP 200; ver §13).
3. `resolveAppOrigin` → `shortUrl`; `null` → a mesma tela de indisponível + log de erro (RC2). QR com `generateQrCodeDataUrl(shortUrl)`; falhou → tela sem QR + aviso (P1b).
4. Mostra: link curto, destino (texto escapado pelo React), estado ("ativo" ou o motivo), "N de M cliques · esgotado" ou "N cliques" (RC8), expiração, criação, nota "o detalhamento pode ficar um pouco abaixo do total" quando `detailBelowTotal`, dispositivos, top 10 referrers + "outros" (o balde `null` aparece como "direto ou desconhecido", com a explicação de que apps como WhatsApp não enviam referrer), "pré-visualizado N× por bots" e o gráfico.
5. **Sem `loading.tsx` nesta rota**, para o `notFound()` responder `404` de verdade (com *streaming* já iniciado, o status não muda). **(conferir no `test:http`.)**
6. **Link já desativado:** o estado mostra "Desativado em DD/MM/AAAA às HH:MM" e a página **não** mostra o botão "Desativar" (a ação seria inócua). Links expirados ou esgotados continuam com o botão.

**Textos (`manage-labels.ts`):**

| Função | Saída |
|---|---|
| `describeLinkState(state)` | `Ativo`, `Desativado`, `Expirado`, `Limite de cliques atingido` |
| `formatClickTotal(clickCount, maxClicks, state)` | `8 cliques`, `1 clique`, `3 de 10 cliques`, `10 de 10 cliques · esgotado` |
| `formatDateTimeInSaoPaulo(date)` | `08/10/2026 às 12:05` |
| `describeDevice(device)` | `Celular`, `Computador`, `Tablet`, `Desconhecido` |
| `describeReferrer(host)` | o host, ou `Direto ou desconhecido` para `null` |
| `formatBotPreviews(count)` | `Nenhuma pré-visualização por bots`, `Pré-visualizado 1× por bots`, `Pré-visualizado N× por bots` |

**Página 404 global (`src/app/not-found.tsx`):** título "Página não encontrada", frase "Confira se o endereço foi copiado inteiro." e o link "Criar um novo link" para `/`. É a mesma para token inexistente e fora do formato.

**Gráfico (`daily-clicks-chart.tsx`, S5):** Server Component; uma `<div>` por dia com altura `count / max * 100%` (**`0%` quando o maior dia é 0**, nunca `NaN`), `title="DD/MM: N cliques"` (`1 clique` no singular), rótulo "dias no horário de Brasília" e uma `<table>` "dia × cliques" visualmente oculta (classe `sr-only`) como alternativa em texto.

**Desativação:** `deactivate-link-form.tsx` mostra "Desativar" → "Tem certeza? Não dá para desfazer" → "Sim, desativar", que envia um formulário com o token em `<input type="hidden">` para:

```ts
'use server'
export async function deactivateLink(prev: DeactivateState, form: FormData): Promise<DeactivateState>
// DeactivateState = { status: 'idle' } | { status: 'done'; message: string } | { status: 'error'; message: string }
```

A action só monta as dependências e chama `handleDeactivateLink(form: FormData, deps: { linkService: Pick<LinkService, 'deactivate'>; revalidate: (path: string) => void }): Promise<DeactivateState>` (`src/app/_lib/deactivate-link-handler.ts`), passando o `revalidatePath` como `revalidate`. Campo `token` ausente, como `File` ou fora do formato → a mesma resposta de "não encontrado", sem exceção. `deactivated`/`already-deactivated` → "Link desativado." + `revalidate('/manage/<token>')` (conferir na tarefa que a página atualiza); `not-found` → "Não foi possível desativar: link não encontrado."; `RepositoryUnavailableError` ou erro inesperado → "Não foi possível desativar agora. Tente em alguns minutos." + log (`database-unavailable` ou `unexpected-error`). Sem rate limit (`error-map.md`). CSRF: proteção embutida das Server Actions; **não configurar `serverActions.allowedOrigins`**.

**Headers:** `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex` e `Cache-Control: no-store` pelo `next.config.ts` (§9.4), na regra que vem **depois** da global.

### 8.6 Páginas de status (`status-pages.ts`)

```ts
export type StatusPage =
  | 'not-found' | 'gone-deactivated' | 'gone-expired' | 'gone-exhausted'
  | 'rate-limited' | 'unavailable' | 'limited-preview'
export function statusPageResponse(page: StatusPage, opts?: { retryAfterSeconds?: number; head?: boolean }): Response
```

HTML mínimo em pt-BR com CSS inline, **sem `<script>` e sem interpolar nada da requisição nem do link** (RC6). Headers: `Content-Type: text/html; charset=utf-8`, `Cache-Control: no-store` e, quando houver, `Retry-After`.

| Página | Status | Título | Frase |
|---|---|---|---|
| `not-found` | 404 | Link não encontrado | Este link não existe. Confira se ele foi copiado inteiro. |
| `gone-deactivated` | 410 | Link indisponível | Este link foi desativado por quem o criou. |
| `gone-expired` | 410 | Link indisponível | Este link expirou. |
| `gone-exhausted` | 410 | Link indisponível | Este link atingiu o limite de acessos. |
| `rate-limited` | 429 | Muitos acessos | Muitos acessos em pouco tempo. Aguarde um minuto e tente de novo. |
| `unavailable` | 503 | Serviço indisponível | Serviço indisponível. Tente novamente em instantes. |
| `limited-preview` | 200 | Link de acesso limitado | Abra o link para continuar. |

Todas, menos a `limited-preview`, terminam com o link "Criar um novo link" para `/`. A `limited-preview` leva `<meta property="og:title" content="Link de acesso limitado">`, `<meta property="og:description" content="Abra para continuar">` e `<meta name="robots" content="noindex">`. As frases das páginas 404, 429 e da prévia são texto desta spec; as do 410 e do 503 vêm de `redirect.md`.

## 9. Configuração e setup

Regras: `.agents/rules/architecture-stack.md`, `architecture-persistence.md` (S1), `architecture-testing-ci.md`, `architecture-local-dev.md`, `security-core.md` (RC6), `code-style.md` (S2).

### 9.1 `package.json`

- `"engines": { "node": "24.x" }`, `"private": true`.
- Versões **exatas**, instaladas sempre com `npm install <pacote>@<versão>`: `next@16.3.8`, `react` e `react-dom` na versão que o `next@16.3.8` declara, `prisma@7.10.0`, `@prisma/client@7.10.0`, `@prisma/adapter-pg@7.10.0`, `pg`, `@vercel/functions`, `@upstash/ratelimit`, `@upstash/redis`, `qrcode@1.5.4`; dev: `typescript@6.0.3`, `eslint-config-next@16.3.8`, **`eslint` 9.x** (o `eslint-plugin-import@2.32` e o `eslint-plugin-react@7.37`, dependências do `eslint-config-next`, não aceitam o ESLint 10; verificado em 2026-10-08), `@next/env@16.3.8`, `vitest` (a 5.x que o `min-release-age` aceitar), `@types/*` necessários, `tailwindcss` e `@tailwindcss/postcss` 4.x. O `npx shadcn init`/`add` acrescenta as dependências dos componentes (esperado: `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`, `tw-animate-css` e Radix), conferidas e registradas no plano. Versões que esta spec não fixa são escolhidas na tarefa com `npm view` e registradas no plano (seção "Versões escolhidas" do plano da fatia 1). React: a 19.x mais nova aceita (o `next@16.3.8` declara `^19.0.0`).
- `"allowScripts"`: `prisma`, `@prisma/engines`, `esbuild`, `unrs-resolver` (revisar a cada dependência; o `strict-allow-scripts` acusa o que faltar).
- Scripts:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "postinstall": "prisma generate",
  "db:migrate": "prisma migrate deploy",
  "db:migrate:test": "DATABASE_URL_UNPOOLED=postgresql://shorturl:shorturl-dev@127.0.0.1:5432/shorturl_test prisma migrate deploy",
  "lint": "eslint .",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:http": "next build && vitest run --config vitest.http.config.mts"
}
```

### 9.2 `.npmrc` (versionado, nunca com token)

```ini
save-exact=true
min-release-age=1
strict-allow-scripts=true
```

### 9.3 ESLint (`eslint.config.mjs`, flat config)

Base: a configuração do `eslint-config-next@16.3.8` (core-web-vitals + TypeScript), mais:

- `import/no-extraneous-dependencies: 'error'` (dependência fantasma);
- `react/no-danger: 'error'` (RC6);
- `no-restricted-properties` contra `$queryRawUnsafe` e `$executeRawUnsafe`, e `no-restricted-syntax` contra `Prisma.raw` (RC3);
- `ignores` global com `src/data/generated/**` (código gerado).
- **S2, nesta ordem** (no flat config, a última configuração que casa com o arquivo define as opções da regra):
  1. `files: ['src/**/*.{ts,tsx}']`, `ignores: ['src/data/**']`: `no-restricted-imports` barrando o client gerado (`@/data/generated/*` e caminho relativo até `data/generated/`), `@prisma/*` e `pg` (mensagem: "Só src/data/ importa o Prisma e o pg.");
  2. `files: ['src/domain/**/*.ts']`, `ignores: ['src/domain/**/*.test.ts']`: `no-restricted-imports` com **lista branca** (mensagem citando o AD-004). O domínio só importa `./*` e `@/domain/*`; dentro de subpastas (`__fakes__/`), também `../*`, **sem nunca sair de `src/domain/`**. Qualquer pacote (inclusive `node:*`) e qualquer caminho relativo que saia do domínio (`../data/...`, `../infra/...`) é erro.
  - Correção de 2026-10-08: a primeira versão, `group: ['*', '!./*', '!../*', '!@/domain/*']`, deixava o domínio importar `../data/...` e barrava o `vitest` nos testes do domínio. Se o estilo gitignore do `group` não fechar os casos (ressalva da doc sobre reincluir arquivo de diretório excluído), usar `patterns[].regex`.
- **Prova permanente em `eslint.config.test.ts`** (API Node do ESLint, `lintText` com `filePath` simulado), com a tabela de casos da Tarefa 2 do plano da fatia 1: o domínio barra `next/server`, `@upstash/redis`, `node:crypto`, `@/data/generated/...`, `../data/...`, `../infra/...` e `@/app/...`, e aceita `./link`, `@/domain/link` e `../ports` dentro de `__fakes__/`; os testes do domínio importam `vitest`; fora de `src/data/`, `@prisma/client`, `pg` e o client gerado são erro; mais `react/no-danger`, as regras do SQL cru, `import/no-extraneous-dependencies` (`pngjs`, transitiva não declarada) e o `ignores` do código gerado.

### 9.4 `next.config.ts`

```ts
import type { NextConfig } from 'next'
import { PHASE_DEVELOPMENT_SERVER } from 'next/constants'

export default function nextConfig(phase: string): NextConfig {
  // trava 2 (architecture-local-dev.md)
  if (process.env.USE_LOCAL_FAKES === 'true' && phase !== PHASE_DEVELOPMENT_SERVER) {
    throw new Error('USE_LOCAL_FAKES ligado fora do next dev: mova-o para o .env.development.local')
  }
  // trava das chaves na Vercel (RC4)
  if (process.env.VERCEL_ENV) {
    const missing = ['UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'SAFE_BROWSING_API_KEY']
      .filter((name) => !process.env[name])
    if (missing.length > 0) throw new Error(`Variáveis ausentes na Vercel: ${missing.join(', ')}`)
  }
  return {
    poweredByHeader: false,
    async headers() {
      return [
        { source: '/:path*', headers: securityHeaders(phase) },
        {
          source: '/manage/:token',
          headers: [
            { key: 'Referrer-Policy', value: 'no-referrer' },
            { key: 'X-Robots-Tag', value: 'noindex' },
            { key: 'Cache-Control', value: 'no-store' },
          ],
        },
      ]
    },
  }
}
```

`securityHeaders(phase)` (RC6, receita "Without Nonces" do Next 16):

| Header | Valor |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline'` (+ `'unsafe-eval'` só em `PHASE_DEVELOPMENT_SERVER`)`; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

A regra da gestão vem por último: "If two headers match the same path and set the same header key, the last header key will override the first" (Next, "next.config.js: headers"). O `test:http` confere os headers globais também nas respostas 404/410 do Route Handler do redirect. `poweredByHeader: false` remove o `X-Powered-By` (detalhe desta spec). Fontes servidas pelo próprio site (`next/font` com arquivo local ou do Google baixado no build), por causa do `font-src 'self'`.

### 9.5 `prisma.config.ts`

```ts
import { loadEnvConfig } from '@next/env'
import { defineConfig } from 'prisma/config'

loadEnvConfig(process.cwd(), true) // mesma precedência do next dev; não sobrescreve o shell

export default defineConfig({
  schema: 'prisma/schema.prisma',
  migrations: { path: 'prisma/migrations' },
  datasource: { url: process.env.DATABASE_URL_UNPOOLED }, // process.env, nunca env() (S1)
})
```

Sem a URL, o `prisma generate` (que não usa banco) continua funcionando, e o `migrate` falha com erro explícito. Se o tipo do `defineConfig` não aceitar `undefined`, passa `process.env.DATABASE_URL_UNPOOLED ?? ''` (conferir na tarefa).

### 9.6 `vercel.json` (S1)

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "npm run db:migrate && npm run build"
}
```

O client já foi gerado no `postinstall` da instalação. Migration só aditiva (RC1).

### 9.7 `compose.yml` e `docker/postgres-init.sql`

```yaml
services:
  postgres:
    image: postgres:<MAJOR> # a mesma major do projeto no Neon, definida no setup
    environment:
      POSTGRES_USER: shorturl
      POSTGRES_PASSWORD: shorturl-dev # só desenvolvimento local; não é segredo
      POSTGRES_DB: shorturl
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - ./docker/postgres-init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shorturl"]
      interval: 2s
      retries: 15
```

`postgres-init.sql`: `CREATE DATABASE shorturl_test;`. **Dois bancos no mesmo container**: `shorturl` para o `npm run dev` e `shorturl_test` para os testes. Detalhe desta spec: o `TRUNCATE` dos testes nunca apaga os links criados à mão no `npm run dev`.

### 9.8 Vitest

- **`vitest.config.mts`:** `resolve: { tsconfigPaths: true }`; `test.env.DATABASE_URL` fixo em `postgresql://shorturl:shorturl-dev@127.0.0.1:5432/shorturl_test` (os testes nunca leem `.env*` nem conhecem a URL do Neon); dois `projects`: `unit` (`src/**/*.test.{ts,tsx}` e os `*.test.ts` da raiz, como `next.config.test.ts` e `eslint.config.test.ts`, exceto `*.int.test.ts`; o `.tsx` usa o JSX automático do React, conferido na fatia 3) e `integration` (`src/**/*.int.test.ts`, `fileParallelism: false`, `setupFiles: ['tests/setup/integration-setup.ts']`, que **recusa rodar se o host da URL não for `127.0.0.1` ou `localhost`** e faz `TRUNCATE click_events, links RESTART IDENTITY` antes de cada arquivo, com `pg`).
- **`vitest.http.config.mts`:** `include: ['tests/http/**/*.http.test.ts']`, `fileParallelism: false`, `globalSetup` (`tests/http/global-setup.ts`) que **recusa subir se `http://127.0.0.1:3000` já responder** (um `npm run dev` esquecido faria os testes rodarem contra os falsos), sobe `next start -p 3000` (`child_process.spawn`) com `DATABASE_URL` do banco de teste e `APP_ORIGIN=http://localhost:3000` e **sem `USE_LOCAL_FAKES`** no ambiente, espera a porta responder (até 30 s) e derruba o processo no fim. Os links de teste são gravados direto no banco pelo Prisma (`tests/http/helpers/database.ts`, com `createPrismaClient`).
- O banco de teste recebe as migrations com `npm run db:migrate:test` na máquina local; no CI, `npm run db:migrate` já aponta para o `shorturl_test` pelas variáveis do job.

### 9.9 `.env.example`

```dotenv
# Copie para .env.development.local (só o `next dev` lê esse arquivo; o Git ignora).
# USE_LOCAL_FAKES troca o Upstash e o Google por falsos locais. Só vale no `next dev`:
# o next build e o next start falham se ele estiver ligado (trava 2).
USE_LOCAL_FAKES=true
DATABASE_URL=postgresql://shorturl:shorturl-dev@127.0.0.1:5432/shorturl
DATABASE_URL_UNPOOLED=postgresql://shorturl:shorturl-dev@127.0.0.1:5432/shorturl
APP_ORIGIN=http://localhost:3000
# Chaves reais (deixe em branco com USE_LOCAL_FAKES=true):
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
SAFE_BROWSING_API_KEY=
```

### 9.10 CI (`.github/workflows/ci.yml`)

```yaml
name: CI
on:
  push:
    branches: ["**"]
  pull_request:
permissions:
  contents: read
jobs:
  ci: # nome usado pelo ruleset e pelos Deployment Checks: renomear exige atualizar os dois painéis
    runs-on: ubuntu-24.04
    services:
      postgres:
        image: postgres:<MAJOR>
        env: { POSTGRES_USER: shorturl, POSTGRES_PASSWORD: shorturl-dev, POSTGRES_DB: shorturl_test }
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U shorturl" --health-interval 2s --health-retries 15
    env:
      DATABASE_URL: postgresql://shorturl:shorturl-dev@127.0.0.1:5432/shorturl_test
      DATABASE_URL_UNPOOLED: postgresql://shorturl:shorturl-dev@127.0.0.1:5432/shorturl_test
    steps:
      - uses: actions/checkout@<SHA completo> # vX.Y.Z
      - uses: actions/setup-node@<SHA completo> # vX.Y.Z
        with: { node-version: "24.x", cache: npm }
      - run: npm ci
      - run: npm run db:migrate
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
      - run: npm run test:http
```

Nenhum segredo. Os SHAs são buscados na tarefa, no release de cada ação, com a versão no comentário.

### 9.11 Configuração em painel (fatia 1, com o Rafael)

- **Neon:** projeto com a major do Postgres escolhida (a mesma do `compose.yml`), na **mesma região da função da Vercel**; Neon-Managed Integration na Vercel, com "Automatically delete obsolete Neon branches" (RC1).
- **Vercel:** projeto importado do GitHub, Node 24.x; variáveis `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` e `SAFE_BROWSING_API_KEY` em **Production e Preview** (RC4); Standard Protection ligada; Deployment Checks com o job `ci`; conferir com um commit que falha de propósito que o `*.vercel.app` fica retido.
- **GitHub:** ruleset na `main` exigindo o job `ci`, sem aprovação de revisor.
- **Upstash:** banco Redis na mesma região. **Google Cloud:** API key restrita à Safe Browsing API (pré-requisito do Rafael).
- **Conferências:** `curl -I` para o HSTS (RC6); janela anônima para os `*.vercel.app` (RC2).

## 10. Mapa de erros

A fonte é `.agents/context/error-map.md` (mensagens exatas e o que é logado). Esta spec só define onde cada uma é produzida: rodada de formato e rate limit na entrada (§8.2, §8.3), regras no domínio por código (§5.5, §5.7), tradução para texto em `toCreateLinkErrorState` (§8.3), respostas do redirect em `statusPageResponse` (§8.6).

## 11. Plano de testes

Regras: `.agents/rules/architecture-testing-ci.md`. TDD em todas as tarefas: o teste falha antes da implementação. Os casos com valores concretos de cada teste, inclusive os do "Review Focus" (entradas que esta lista não cobria), estão nas tarefas dos três planos (`docs/superpowers/plans/2026-10-08-short-url-mvp-*.md`).

**Configuração (unitários, na raiz):** `next.config.test.ts` (trava 2, trava das chaves, headers e a ordem das regras) e `eslint.config.test.ts` (S2, RC3, RC6, dependência fantasma). **Schema (integração):** `src/data/schema.int.test.ts` confere tipos, índices, FK `RESTRICT`, o enum e que `click_events` não tem coluna de IP nem de UA.

**Unitários (Vitest, sem rede nem banco):**

- **Domínio com fakes** (`LinkRepository` e `ClickEventRepository` em memória, `UrlThreatChecker` programável, `Clock` fixo): `create` (sucesso; erros juntos de todos os campos; o Google não é consultado com erro de regra; `threat`; `unavailable`; 3 colisões; 2 colisões e sucesso); `deactivate` (sucesso, já desativado mantém a data, token inexistente, formato inválido); `resolve` (`visit` e `peek` em cada estado; precedência do 410; invariante).
- **Tabelas das funções puras:** `isValidSlugFormat`; `generateSlug` (alfabeto, tamanho, distribuição grosseira em 10 mil amostras); formato e hash do token (vetor fixo de SHA-256); `isPreviewBot` (UAs reais das 7 plataformas e dos navegadores embutidos do Facebook e do Instagram); `classifyDevice`; `extractReferrerHost`; `classifyLink`; `UrlValidator` (R1 a R6, IDN `аpple.com` → punycode, IPv4 em octal/hex, todas as faixas da §5.5, IPv6 literal, `localhost:3000`, `exemplo.com/promo`, 2048 × 2049 caracteres no `href`); tempo em São Paulo (fim do dia; dezembro de 2018 com `-02:00`; "hoje" perto da meia-noite UTC; limite de 5 anos com 29 de fevereiro); `dailyWindow` e `buildClickStats` (dias vazios, top 10 + outros, `detailBelowTotal`).
- **Entrada:** `parseCreateLinkForm` (`trim()`, `"10 "`, `"10abc"`, `"1e3"`, `"-5"`, `"2.5"`, `2026-02-30`, duração forjada, duração e data juntas); `toCreateLinkErrorState` (cada linha do `error-map.md`); `rateLimitKey` (IPv4, IPv6 com `::`, maiúsculas, mapeado, inválido, ausente, `development`); `resolveAppOrigin` (cada combinação de variáveis, `null`); `statusPageResponse` (status, headers, ausência de `<script>`); ponto de montagem (configuração ausente → adaptador indisponível; trava 1).
- **Infra:** `canonicalize` e `buildExpressions` com os exemplos das docs v4 e v5 (`a.b.c.d.e.f.com`, `example.co.uk`, IP, query, `/../`, escapes repetidos); `SafeBrowsingUrlThreatChecker` com `fetch` falso (hit, miss, detalhe `CANARY`, `threatType` desconhecido, timeout, 429, JSON inválido, cache válido sem rede, cache vencido com relógio injetado, teto do cache, a URL da chamada nunca aparece em log); `LocalFakeUrlThreatChecker`; `InMemoryRateLimiter` com relógio injetado.

**Integração (Postgres do Docker, `*.int.test.ts`):**

- `PrismaLinkRepository`: `insert` e `slug-taken`; `consumeClick` em cada estado; `deactivateByTokenHash` idempotente; tradução de erro com o banco parado (§6.5).
- **Concorrência do limite:** link com `maxClicks = 100`; 150 chamadas simultâneas de `consumeClick` por um pool com 20 conexões → exatamente 100 sucessos e `click_count = 100`. Repetido 5 vezes no mesmo teste.
- `PrismaClickEventRepository.getStats`: agrupamentos sem `BOT`; dia em São Paulo (clique às 23h30 de Brasília cai no dia certo); tipo `bigint` convertido.

**HTTP (`npm run test:http`, `next start` + Postgres do Docker, `fetch` nativo):**

- `302` com `Location` e `Cache-Control: no-store`; `404` (slug inexistente e fora do formato); `410` com cada motivo; `HEAD` não incrementa `click_count` e não grava evento; bot recebe a página neutra num link com limite e não incrementa.
- Página de gestão: `200` com token válido; `404` com token inexistente e fora do formato; headers `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex` e `Cache-Control` contendo `no-store`.
- Headers globais (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`) em `/` e nas respostas 404 e 410 do redirect.

**Roteiro manual (fatias 2 e 3):** criar com cada combinação de opções; aviso `http:`; aviso da R7 com a URL de teste do Google (falso local); copiar e baixar; `beforeunload` antes e depois de copiar; F5 descarta o card; QR lido pela câmera do celular; desativar com confirmação.

## 12. Fatias

Cada fatia tem plano, branch e PR próprios e termina com o site publicado (`code-style.md`, "Branches e fatias").

| Fatia | Branch | Entrega |
|---|---|---|
| 1 | `feat/mvp-1-base` | §9 inteira (scaffolding Next + Tailwind + shadcn/ui, `.npmrc`, ESLint com S2, `next.config.ts` com travas e headers, Prisma com schema e migration `init`, `vercel.json`, `compose.yml`, Vitest, CI); painéis (§9.11); **domínio completo (§5) com os testes unitários**; home provisória publicada. **Primeira PR, feita em conjunto.** |
| 2 | `feat/mvp-2-create-redirect` | §6.2, §6.3, §6.5 e o `record` da §6.4; §7 inteira; §8.1 a §8.4 e §8.6; ponto de montagem (§4.3) e logs (§4.4); testes de integração, concorrência e HTTP do redirect; roteiro manual da criação. |
| 3 | `feat/mvp-3-manage` | `getStats` (§6.4); §8.5 com o gráfico; testes HTTP da gestão; roteiro manual; **README** (descrição, stack, diagrama de system design, link para o ADR, "como escalaria", rodar localmente e os testes, "um link por canal", aviso de falsos positivos e negativos do Google, limitações da §13). |

## 13. Limitações documentadas

Entram no README. Vindas do design: scanners de e-mail com UA de navegador consomem links com limite; iPad com Safari aparece como `DESKTOP`; `click_count` pode ficar acima da soma dos eventos (evento perdido depois do 302); logs da Vercel (1 h no Hobby) e o histórico do navegador guardam o token; a blocklist não pega golpe novo nem site que vira golpe depois; resposta perdida na rede perde o token; a R3 não cobre os endereços por deploy e por branch (RC2); a CSP aceita `'unsafe-inline'` (RC6); o `x-real-ip` só é confiável na Vercel (RC5); a R4 não resolve DNS (RC10).

Vindas desta spec:

- **Safe Browsing:** sufixos de host pela regra da v4, sem a Public Suffix List (S3); um site listado dentro do `cacheDuration` escapa até o cache vencer (S4); fail-closed em vez do "seguro na falha" do Google (B1).
- **Entrada com porta e sem protocolo** (`site.com:8080/x`) é lida como protocolo e recusada pela R1; o usuário digita o `https://`.
- **Página de gestão com o banco fora** responde HTTP 200 com a mensagem de indisponível (uma página do App Router não tem como responder 503; só o `notFound()` muda o status).
- **Referrers:** a tela mostra os 10 maiores e soma o resto em "outros".

## 14. Notas sobre o AD-004

O ADR é append-only, e nenhuma das duas mudanças abaixo passa nos três critérios de entrada (`spec-workflow.md` §2), então ficam registradas aqui:

- **O `QrCodeGenerator` saiu do domínio** e virou `src/app/_lib/qr-code.ts`: o QR é apresentação do link curto, e a `qrcode` é dependência de terceiros que o domínio não pode importar (`architecture-layers.md`).
- **Os adaptadores ganharam a pasta `src/infra/`** (B2), ao lado de `src/data/`, para serviços externos que não são o banco.
- O AD-004 lista `UrlValidator`, `SlugGenerator`, `ClickTracker` e `LinkService`; esta spec acrescenta `RedirectService` e as funções puras de §5.3, §5.4 e §5.9, todas dentro do domínio.

## 15. Alternativas consideradas e por que foram descartadas

Resumo; o motivo completo está no arquivo indicado.

| Tema | Descartado | Por quê | Fonte |
|---|---|---|---|
| Hospedagem | API separada no Render + SPA | hibernação do free tier, dois deploys | AD-001 |
| ORM | Drizzle; Supabase | curva e prazo; traz o que não se usa | AD-002 |
| Autorização | contas com login | segurança de fachada no modelo de ameaça | AD-003 |
| Camadas | regra nos handlers | acopla ao framework, teste exige banco | AD-004 |
| Driver | `@prisma/adapter-neon` | abre e fecha por request; prende ao Neon | `architecture-persistence.md` |
| Migration | build local, job no CI com segredo, preview na produção, script `build`, painel | risco à produção, quebra o CI sem segredos, fora do repositório | `architecture-persistence.md` (RC1, S1) |
| Testes | `node:test`, Jest, PGlite, branch do Neon, Playwright | ditaria o código; ESM experimental; concorrência falsa; risco à produção; peso | `architecture-testing-ci.md` |
| Pacotes | pnpm 11, bun | suporte da Vercel, ferramenta a mais | `architecture-stack.md` |
| Redirect | 301; redirect para página React; `405` no `HEAD` | perde analytics; perde 404/410; acusa link quebrado | `redirect.md` |
| Clique | gravar antes de responder; CTE | analytics derrubaria o link | `redirect.md` |
| Bots | `isbot` | dependência para ~8 padrões | `redirect.md` |
| Token | hash lento; texto puro; token no fragmento; "cole seu token" | não indexável; dump expõe tudo; dashboard no cliente; usabilidade | `security-token.md` |
| Rate limit | rigoroso; folgado; endereço IPv6 completo; `/48`; chave `unknown` | bloqueia pessoas; deixa robôs; inútil; junta clientes; 429 global | `security-rate-limit.md` |
| Blocklist | `urls.search`, Web Risk, URLhaus; fail-open; PSL (`tldts`); sem cache; cache no Upstash | URL sai do servidor; cota esgotável; dependência; descumpre o protocolo | `url-validation.md`, `security-blocklist.md` |
| Validação | só HTTPS; DNS na criação; lista de DNS curinga; recusar IDN | ganho nulo; latência e proteção parcial; manutenção; barra `.br` com acento | `url-validation.md` |
| Expiração | `datetime-local`; só durações | sem fuso; não cobre "até o dia 30" | `link-lifecycle.md` |
| Modelo | UUID v7; slug como PK; `IDENTITY`; UA cru; URL completa do referrer | tamanho; acoplamento; migration à mão; fingerprinting; PII de terceiros | `data-model.md` |
| Gráfico | Recharts (Chart do shadcn/ui); TypedSQL; contar no TypeScript | 11 dependências no navegador; exige banco no CI; tráfego | `manage-page.md`, `data-model.md` |
| CSP | nonce via `proxy.ts`; só headers simples; SRI | todas as páginas dinâmicas; não barra script externo; experimental | `security-core.md` |
| Lint do AD-004 | só review; lista negra | atalho passa com testes verdes; pacote novo passa | `code-style.md` (S2) |
| Dev local | `.env.local`; `.env.development` versionado; falso automático | quebra o build; chave publicada por engano; falha silenciosa | `architecture-local-dev.md` |

## 16. Requisitos rastreados

A coluna "Tarefa" aponta para as tarefas dos planos (preenchida em 2026-10-08): P1 = `2026-10-08-short-url-mvp-1-base.md`, P2 = `…-mvp-2-create-redirect.md`, P3 = `…-mvp-3-manage.md`, em `docs/superpowers/plans/`. Status: `Planejado` → `Implementado` no fim da fatia que fecha o requisito.

| ID | Requisito | Fatia | Tarefa | Status |
|---|---|---|---|---|
| RF01 | Encurtar uma URL válida e receber link curto, link de gestão (uma vez) e QR | 2 | P2: T18–T21 | Planejado |
| RF02 | Limite de cliques opcional, de 1 a 1.000.000 | 1 (regra) · 2 (tela) | P1: T7, T14 · P2: T16, T20 | Planejado |
| RF03 | Expiração opcional: duração pronta ou fim do dia em Brasília, com o rótulo da P7 | 1 · 2 | P1: T10, T14 · P2: T16, T20 | Planejado |
| RF04 | Validação R1 a R6 com mensagem por regra | 1 · 2 | P1: T11, T14 · P2: T17, T20 | Planejado |
| RF05 | R7: recusar URL do Safe Browsing com aviso "suspeito" e atribuição ao Google | 2 | P2: T5, T6, T7, T17 | Planejado |
| RF06 | Aviso de destino `http:` | 2 | P2: T19, T21 | Planejado |
| RF07 | Redirect 302 `no-store`; 404; 410 com motivo; 429; 503 | 2 | P1: T16 · P2: T14, T15 | Planejado |
| RF08 | Registro do clique (dispositivo, referrer, data) fora do caminho crítico, só com link ativo | 2 | P2: T4, T15 | Planejado |
| RF09 | Bots de preview e `HEAD` não consomem nem revelam o destino de link com limite | 2 | P1: T16 · P2: T15 | Planejado |
| RF10 | Gestão: total, dispositivos, referrers, gráfico de 30 dias (só humanos), bots à parte | 3 | P1: T17, T18 · P3: T1–T4 | Planejado |
| RF11 | QR na página de gestão | 3 | P3: T3, T4 | Planejado |
| RF12 | Desativação irreversível, com confirmação e idempotente | 1 (regra) · 3 (tela) | P1: T15 · P3: T5 | Planejado |
| RF13 | Token exibido uma vez, em destaque, com `beforeunload` até copiar | 2 | P2: T21 | Planejado |
| RF14 | `npm run dev` sem chaves, com falsos locais e as duas travas | 1 (travas) · 2 (falsos) | P1: T3 · P2: T7, T11, T13 | Planejado |
| RNF01 | Limite de cliques respeitado sob concorrência (UPDATE atômico, teste com Postgres real) | 2 | P2: T3 | Planejado |
| RNF02 | Rate limit 10/min + 100/dia na criação e 300/min no redirect, `/64`, fail-open no redirect e fail-closed na criação | 2 | P2: T10–T12, T15, T19 | Planejado |
| RNF03 | Headers globais e CSP (RC6); headers da gestão | 1 · 3 | P1: T3 · P3: T4 | Planejado |
| RNF04 | Token só como hash no banco; nunca em log, cookie, `localStorage` ou redirect | 1 · 2 | P1: T6, T9 · P2: T8, T19, T21 | Planejado |
| RNF05 | IP nunca persistido; UA cru nunca persistido | 2 | P1: T6 · P2: T4, T15 | Planejado |
| RNF06 | AD-004 garantido por lint (S2) | 1 | P1: T2 | Planejado |
| RNF07 | CI sem segredos, ações por SHA, `contents: read`; publicação só com o CI verde | 1 | P1: T19–T21 | Planejado |
| RNF08 | Supply chain: `.npmrc` endurecido, `allowScripts`, versões exatas, sem dependência recusada | 1 | P1: T1 | Planejado |
| RNF09 | Timeouts: banco 5 s, Upstash 1 s, Google 2 s | 2 | P2: T1, T6, T12 | Planejado |
| RNF10 | Migrations aditivas no `buildCommand`; preview com branch do Neon e Standard Protection | 1 | P1: T6, T20 | Planejado |
| RNF11 | Interface e README em pt-BR | 2 · 3 | P2: T14, T17, T20, T21 · P3: T3, T4, T6 | Planejado |
| RNF12 | README completo do PRD, com as limitações da §13 | 3 | P3: T6 | Planejado |
