---
trigger: always_on
---
# Arquitetura — camadas e decisões não negociáveis

## Camadas e organização de pastas

São três camadas no servidor (entrada, domínio e adaptadores), e as dependências sempre apontam para dentro (AD-004). A camada de adaptadores fica em **duas pastas**, `src/data/` (banco) e `src/infra/` (serviços externos), decididas na B2 em 2026-09-30. A estrutura abaixo é uma proposta, a confirmar na spec:

```
src/
├── app/          → entrada: páginas, Route Handlers, Server Actions (única camada com next/*)
│   └── _lib/     → auxiliares fora do roteamento: templates HTML, QR code, rate limit, origem canônica
├── domain/       → regras de negócio em TypeScript puro + interfaces (portas)
├── data/         → adaptador do banco: Prisma (único lugar que importa Prisma)
│   └── generated/prisma/   → client gerado (não versionado)
├── infra/        → adaptadores de serviços externos (ex.: Google Safe Browsing)
└── components/   → componentes React (shadcn/ui em components/ui/)
```

Direção das dependências: `app` → `domain` ← `data` e `infra`. O domínio não importa nenhuma das outras pastas; `data` e `infra` implementam as interfaces dele, e a entrada monta tudo, injetando os adaptadores pelo construtor.

- `src/app/` — **entrada**: Pages, Route Handlers (ex.: `[slug]/route.ts` para o redirect) e Server Actions. É a única camada que importa `next/*`. O guarda de rate limit fica aqui, antes de qualquer chamada ao domínio. O redirect exporta `GET` e `HEAD`, com um `HEAD` próprio para o Next não executar o `GET` e consumir o link, e grava o evento de clique com `after()` de `next/server`. Os templates HTML do `404`, do `410` e da página neutra dos bots ficam num módulo auxiliar (ex.: `src/app/_lib/`). Ver `.agents/context/redirect.md`, "Fluxo". A geração do QR code também fica aqui: o QR é uma apresentação do link curto que o domínio devolve, não regra de negócio, e a lib `qrcode` é dependência de terceiros que o domínio não pode importar. Fica num módulo auxiliar fora das rotas (ex.: pasta privada `src/app/_lib/`, que o App Router exclui do roteamento). O QR é gerado sob demanda a partir da URL curta e não é persistido. Duas telas usam a mesma função: o card de criação e a página de gestão (P1b). O formato é PNG em data URL com 512 px (ver `.agents/context/link-creation.md`, "QR code").
- `src/domain/` — **domínio**: regras de negócio em TypeScript puro (`LinkService`, `SlugGenerator`, `UrlValidator`, `ClickTracker`) e as interfaces que o domínio exige, como `LinkRepository`, `UrlThreatChecker` (R7) e `Clock` (B-1, relógio injetado para os testes).
- `src/data/` — **dados**: implementações das interfaces do domínio com Prisma (ex.: `PrismaLinkRepository`) e o client Prisma singleton. É o único lugar que importa Prisma.
  - O client gerado pelo Prisma 7 fica em `src/data/generated/prisma/` (`output` do generator `prisma-client`) e é importado de lá, não de `@prisma/client`. Assim, o próprio caminho do import denuncia uma violação do AD-004, e o lint a barra (S2, `code-style.md`).
  - A pasta gerada não é versionada (`.gitignore`), e o `postinstall` roda `prisma generate` (S1, `architecture-persistence.md`). Sem isso, o deploy falha com `Cannot find module`.
- `src/infra/` — **integrações externas** (B2, decidida em 2026-09-30): adaptadores que implementam interfaces do domínio falando com serviços de fora que não são o banco. Hoje: `SafeBrowsingUrlThreatChecker` (arquivo `safe-browsing-url-threat-checker.ts`), que implementa o `UrlThreatChecker` da R7 com `fetch` e `crypto.subtle` nativos e cache em memória (S4), e o `LocalFakeUrlThreatChecker`, usado só no `npm run dev` (ver `architecture-local-dev.md`). É o lugar das evoluções documentadas (Google Web Risk no lugar do Safe Browsing, fila com retry para os eventos de clique).
  - Motivo da pasta separada: `src/data/` continua com um papel só ("o único lugar que importa Prisma"), e o nome de cada pasta diz o que tem dentro. Descartado: pôr o adaptador em `src/data/`, que viraria "banco e serviços externos".
  - O rate limit (Upstash) **não** vai para cá: é um guarda da camada de entrada (AD-004), não uma interface do domínio.
- `src/components/` — componentes React. Os do shadcn/ui ficam em `src/components/ui/`.

## Decisões não-negociáveis
- O domínio nunca importa `next/*`, o client do Prisma nem nada de `src/data/` ou `src/infra/`. Ele recebe as dependências pelo construtor (AD-004). O lint barra qualquer import de pacote no domínio (S2, `code-style.md`).
- Nada de SQL montado por concatenação de string. Acesso ao banco só via Prisma, com queries parametrizadas. **SQL cru (RC3, decidido em 2026-10-07)** só quando a API do Prisma não alcança, só com `$queryRaw` em template marcado (cada `${}` vira parâmetro de *prepared statement*) e só em `src/data/`. `$queryRawUnsafe`, `$executeRawUnsafe` e `Prisma.raw` são barrados pelo lint. Hoje o único caso é o gráfico diário (`data-model.md`). Base: Prisma v7, "Raw queries", "SQL injection prevention".
- O redirect usa **HTTP 302 + `Cache-Control: no-store`**, nunca 301 (o 301 é cacheado pelo navegador e perde analytics, expiração e desativação).
- A checagem de desativação, de limite de cliques e de expiração é feita junto com o incremento, numa única operação atômica no banco (evita race condition).
- O slug é aleatório (CSPRNG), nunca sequencial ou enumerável.
- Sem login (AD-003). A autorização sobre um link é a posse do token de gestão.
