# Modelo de dados (fechado; schema na spec, §6.1)

Parte do contexto de domínio, lido sob demanda pelo índice do `AGENTS.md`. O como (SQL, tipos, regex, nomes de método) fica na spec do MVP, `docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`, citada aqui como "spec, §N".

Decidido:

- **Chaves primárias internas inteiras**: `links.id` é `Int` (`SERIAL` no Postgres) e `click_events.id` é `BigInt` (`BIGSERIAL`), ambos com `@default(autoincrement())`, que é o que o Prisma gera. Os identificadores públicos são o `slug` e o token, então o id nunca sai do servidor e "sequencial é enumerável" não se aplica. As chaves ficam as menores possíveis, e a FK de cada evento ocupa 4 bytes. O `BigInt` não é serializável em JSON, o que é inofensivo porque o id de evento nunca sai da camada de dados. Descartados: UUID v7 (16 bytes na tabela de alto volume) e o slug como PK natural (acopla o identificador público às relações).
  - **`SERIAL` em vez de `IDENTITY` (decidido em 2026-09-28).** O `IDENTITY` (`GENERATED ALWAYS`, padrão SQL, recomendado pela wiki do Postgres em "Don't Do This") recusa um `INSERT` com id manual; o `SERIAL` aceita, e o id manual colide depois com a sequência (`duplicate key`). Mas o Prisma não gera `IDENTITY`: seria preciso editar à mão toda migration que criasse tabela, e esse passo esquecido vira divergência silenciosa. No nosso desenho só o `PrismaLinkRepository` insere, e sempre sem id, então a proteção extra do `IDENTITY` não cobre nenhum caminho real. Evolução possível: uma migration manual que converte as colunas para `IDENTITY`.
- **`slug` é `text` com `UNIQUE`**: sem diferença de desempenho em relação a `varchar(n)` no Postgres. O tamanho é validado no domínio.
- **`manage_token_hash` é `BYTEA` (32 bytes, SHA-256) com `UNIQUE`**: ver `.agents/rules/security-token.md`.
- **`destination_url` é imutável**: sem `updated_at` nem histórico de destinos (ver PRD).
- **`click_count` duplicado em `links`**: é a fonte de verdade do limite, via UPDATE atômico. `click_events` serve só para o detalhamento. Pode haver uma pequena divergência, porque o evento é gravado depois da resposta; isso vai documentado. A tela mostra o total pelo `click_count` e avisa quando o detalhamento fica abaixo dele (RC8, `manage-page.md`).
- **`deactivated_at` (timestamp nulo) em vez de booleano**: guarda também quando o link foi desativado.
- **Todos os timestamps são `timestamptz(3)`**: o `DateTime` do Prisma no Postgres é `timestamp` sem fuso por padrão, então precisa de `@db.Timestamptz(3)` explícito.
- **Índice `(link_id, clicked_at)` em `click_events`**: o Postgres não indexa automaticamente o lado que referencia a FK.
- **FK `onDelete: Restrict`**: links nunca são apagados, só desativados.
- **Sem IP em `click_events`**: ver `.agents/rules/security-core.md`, "IP do visitante".
- **Redirect**: o UPDATE atômico com RETURNING é feito pela API do Prisma, sem SQL cru, e o caminho de sucesso usa 1 query; se nada for atualizado, uma leitura pelo slug distingue 404 de 410. Implementação e a nota sobre o Prisma 8 na spec, §6.3.
- **Dispositivo guardado só como categoria**: enum `DeviceType { MOBILE, DESKTOP, TABLET, BOT, UNKNOWN }` (`BOT` identificado antes, por `isPreviewBot`; ver `redirect.md`, "Bots de preview"), classificado no momento do clique por uma função pura do domínio (`classifyDevice`, spec §5.6), sem lib. A ordem é:
  1. `Sec-CH-UA-Mobile` (`?1` → `MOBILE`), um Client Hint que só navegadores Chromium enviam;
  2. regex no `User-Agent` (`iPad|Tablet` → `TABLET`; `Mobi|Android|iPhone` → `MOBILE`);
  3. senão `DESKTOP`;
  4. sem UA → `UNKNOWN`.

  O UA cru não é persistido (minimização; o UA ajuda em fingerprinting). **Limitação documentada:** desde o iPadOS 13, o Safari do iPad manda UA de Mac, então esses iPads aparecem como `DESKTOP`. Android tablets são detectados. Consequência aceita: o histórico não pode ser reclassificado. Descartados: UA cru com classificação na leitura (duplica a regra no SQL e encarece o `GROUP BY`) e categoria + UA cru com retenção curta (exige job agendado, YAGNI).
- **Referrer guardado só como host normalizado**: `referrer_host text NULL`, em que `null` significa direto/desconhecido. É extraído por uma função pura do domínio: `new URL()`, só `http:`/`https:`, `hostname` em minúsculas e sem `www.`; qualquer outra coisa vira `null`. O parsing já é a sanitização, porque o header é input hostil (*referral spam*) e um hostname tem no máximo 253 caracteres. Ganha-se pouco com mais do que o host: desde ~2021 os navegadores usam `strict-origin-when-cross-origin` por padrão e só mandam a origem entre sites diferentes. Apps nativos (WhatsApp, e-mail) não mandam referrer, então o dashboard precisa explicar o balde "direto/desconhecido". Descartados: URL completa e host+caminho (quase nunca chegam e podem expor PII de terceiros ao criador do link, que é anônimo). Evolução: agrupar por domínio registrável (`l.facebook.com` e `m.facebook.com` → `facebook.com`), o que exige a Public Suffix List (dependência recusada por ora; ver S3 em `security-blocklist.md`).
- **O "dia" das estatísticas é o dia em `America/Sao_Paulo`**, com o rótulo "dias no horário de Brasília" no gráfico: o SQL (spec, §6.4) usa o nome IANA, não o offset `-03:00`, para que o banco de fusos absorva uma eventual volta do horário de verão (abolido pelo Decreto 9.772/2019).
  - **Como a consulta é escrita (RC3, decidido em 2026-10-07): `$queryRaw` com template marcado, em `src/data/`.** O `groupBy` do Prisma agrupa por coluna, não por expressão. O tipo do resultado é declarado à mão (o `count` do Postgres volta como `bigint` e é convertido) e conferido pelo teste contra o Postgres do Docker. Regra geral em `architecture-layers.md`. Descartados: TypedSQL (o `prisma generate --sql` exige o banco de pé e migrado, inclusive para checar tipos no CI e na máquina local), coluna `clicked_day` gravada no clique (muda o modelo fechado e impede a evolução para o fuso de quem vê) e contar no TypeScript (um link com 80 mil cliques no mês trafegaria 80 mil linhas a cada abertura da página).
  - Descartados (fuso):
    - UTC: cliques entre 21h e 23h59 de Brasília cairiam no dia seguinte;
    - agregar por hora em UTC e juntar em dias no cliente: falha em fusos com meia hora e duplica lógica no navegador.

  **Evolução documentada:** usar o fuso do navegador de quem vê (`Intl`), enviado por cookie e validado por whitelist com `Intl.supportedValuesOf('timeZone')`. Muda só a query e a entrada, não o schema.

Modelo de dados fechado.
