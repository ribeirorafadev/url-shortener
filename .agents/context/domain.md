# Domínio — short-url

Glossário, regras de negócio e fluxos já decididos. O schema de dados está **em design**: ver "Modelo de dados" no fim do arquivo.

## Glossário

- **Link**: registro que associa um slug a uma URL de destino. Tem limite de cliques e data de expiração, ambos opcionais.
- **Slug**: identificador público e curto do link, a parte que vai na URL (`/aB3xZ9k`).
- **URL de destino**: para onde o visitante é redirecionado. Só `http`/`https`.
- **Token de gestão**: segredo longo e aleatório, gerado na criação e exibido uma única vez. Quem o possui pode ver as estatísticas e desativar aquele link (`/manage/[token]`). Nunca é exposto publicamente.
- **Evento de clique**: registro de um redirecionamento bem-sucedido, com dispositivo, referrer e data/hora.
- **Link ativo / inativo**: é inativo se foi desativado, se passou da data de expiração ou se atingiu o limite de cliques. Um link inativo não redireciona.

## Regras de negócio

- **Slug**: 7 caracteres base62, gerados com CSPRNG (ex.: `crypto.getRandomValues`, nativo), o que dá ~3,5 × 10¹² combinações. Tem constraint `UNIQUE` no banco e, se houver colisão, gera outro. Nunca sequencial, para impedir enumeração.
- **Limite de cliques e expiração**: opcionais. O padrão é sem limite e sem expiração. São funcionalidades de produto (link de uso único, campanha com prazo), **não** proteção. A proteção é o rate limiting.
- **Respostas do redirect**:
  - `302 Found` + `Cache-Control: no-store` quando o link está ativo;
  - `404 Not Found` quando o slug não existe;
  - `410 Gone` quando o link existe mas expirou, esgotou o limite ou foi desativado.
- **Por que 302 e não 301**: o 301 é cacheado pelo navegador. A partir do segundo clique, o navegador vai direto ao destino sem passar pelo servidor, e o sistema perde o analytics e o controle de expiração e desativação.
- **Incremento atômico**: a checagem de limite e de expiração e o incremento do contador acontecem numa única operação no banco. Com a checagem separada do incremento, dois cliques simultâneos com o contador em 99 (limite 100) passariam os dois. A forma de referência é esta (a implementação exata via Prisma fica para a spec):

  ```sql
  UPDATE links
  SET click_count = click_count + 1
  WHERE slug = $1
    AND (max_clicks IS NULL OR click_count < max_clicks)
    AND (expires_at IS NULL OR expires_at > now())
  RETURNING original_url;
  ```

  Se zero linhas forem afetadas, o link não existe ou está inativo. É preciso distinguir os dois casos para responder 404 ou 410.
- **Registro detalhado do clique** (dispositivo, referrer): fica fora do caminho crítico do redirect, gravado depois que a resposta sai. O mecanismo ainda precisa ser confirmado na documentação do Next.js. Em serverless, "fire and forget" pode ser interrompido quando a função termina, então é preciso usar a API própria do framework para trabalho pós-resposta.
- **Token de gestão**: exibido só na resposta de criação. Se o usuário perder o link de gestão, não há recuperação (não existe conta).

## Bots de preview de link (decidido)

Quando um link curto é colado no WhatsApp, Slack, Telegram, X, Facebook, LinkedIn ou Discord, o bot do app faz um `GET` na URL, segue o `302` e lê as meta tags Open Graph do destino para montar o card de prévia. Sem tratamento, o bot infla a contagem de cliques e consome o limite: um link de uso único seria gasto antes de o destinatário clicar.

**Regra:**

- **Link sem limite** (`max_clicks` nulo): todos recebem o `302`, e o preview mostra o destino. O acesso de bot **não incrementa** o `click_count`.
- **Link com limite**: o bot recebe um `200` com uma página neutra, com meta OG genéricas ("Link de acesso limitado · abra para continuar"), **sem revelar o destino e sem consumir nada**. Isso anula o bypass por UA forjado (`curl -A "WhatsApp/2.0"`): quem finge ser bot recebe a página neutra, nunca o destino.
- **Registro:** o acesso de bot vira evento com `device_type = BOT`, sem coluna nova. O dashboard mostra "pré-visualizado N× por bots" à parte e **exclui `BOT` dos totais**. O `click_count` nunca é incrementado por bot.
- **Detecção:** lista própria no domínio (`isPreviewBot(userAgent)`, função pura com regex, testada com UAs reais), cobrindo `WhatsApp/`, `Slackbot`, `facebookexternalhit`, `Twitterbot`, `TelegramBot`, `LinkedInBot` e `Discordbot`. Os padrões vêm da documentação de cada plataforma. A lib `isbot` foi descartada por ser dependência nova para um problema que cerca de 8 padrões resolvem.
- **Limitação documentada:** scanners de segurança de e-mail (Defender Safe Links, Proofpoint, Mimecast) abrem links com UA de navegador comum e continuam consumindo links limitados. A raiz está na RFC 9110, §9.2.1: `GET` é método seguro, e consumir um link num GET é mudança de estado.

**Evolução documentada:** uma página de confirmação para links com limite. O `GET` mostra um botão, e só o `POST` (Server Action) consome o link e redireciona. Resolve também os scanners de e-mail e respeita a semântica de "GET seguro". O custo é um clique a mais para o humano.

## Fluxos

1. **Criar link**: formulário → Server Action → rate limit → validação da URL → gera slug e token → grava via Prisma → o domínio devolve o link curto e o token → a Server Action gera o QR code (camada de entrada) → devolve o link curto, o link de gestão e o QR.
2. **Redirecionar** (caminho mais quente, com leituras ~100× mais frequentes que escritas): `GET /[slug]` → rate limit → operação atômica no banco → `302`, `404` ou `410` → registra o evento de clique fora do caminho crítico.
3. **Gerenciar**: `GET /manage/[token]` → busca o link pelo token (nunca pelo slug) → agrega os cliques no Postgres (`COUNT`/`GROUP BY` por dispositivo, referrer e dia) → dashboard renderizado no servidor → desativação via Server Action.

## Modelo de dados (em design; consolidar na spec)

Decidido:

- **Chaves primárias internas inteiras**: `links.id` é `Int` (`SERIAL` no Postgres) e `click_events.id` é `BigInt` (`BIGSERIAL`), ambos com `@default(autoincrement())`, que é o que o Prisma gera. Os identificadores públicos são o `slug` e o token, então o id nunca sai do servidor e "sequencial é enumerável" não se aplica. As chaves ficam as menores possíveis, e a FK de cada evento ocupa 4 bytes. O `BigInt` não é serializável em JSON, o que é inofensivo porque o id de evento nunca sai da camada de dados. Descartados: UUID v7 (16 bytes na tabela de alto volume) e o slug como PK natural (acopla o identificador público às relações).
  - **`SERIAL` em vez de `IDENTITY` (decidido em 2026-09-28).** O `IDENTITY` (`GENERATED ALWAYS`, padrão SQL, recomendado pela wiki do Postgres em "Don't Do This") recusa um `INSERT` com id manual; o `SERIAL` aceita, e o id manual colide depois com a sequência (`duplicate key`). Mas o Prisma não gera `IDENTITY`: seria preciso editar à mão toda migration que criasse tabela, e esse passo esquecido vira divergência silenciosa. No nosso desenho só o `PrismaLinkRepository` insere, e sempre sem id, então a proteção extra do `IDENTITY` não cobre nenhum caminho real. Evolução possível: uma migration manual que converte as colunas para `IDENTITY`.
- **`slug` é `text` com `UNIQUE`**: sem diferença de desempenho em relação a `varchar(n)` no Postgres. O tamanho é validado no domínio.
- **`manage_token_hash` é `BYTEA` (32 bytes, SHA-256) com `UNIQUE`**: ver `.agents/rules/security.md`.
- **`destination_url` é imutável**: sem `updated_at` nem histórico de destinos (ver PRD).
- **`click_count` duplicado em `links`**: é a fonte de verdade do limite, via UPDATE atômico. `click_events` serve só para o detalhamento. Pode haver uma pequena divergência, porque o evento é gravado depois da resposta; isso vai documentado.
- **`deactivated_at` (timestamp nulo) em vez de booleano**: guarda também quando o link foi desativado.
- **Todos os timestamps são `timestamptz(3)`**: o `DateTime` do Prisma no Postgres é `timestamp` sem fuso por padrão, então precisa de `@db.Timestamptz(3)` explícito.
- **Índice `(link_id, clicked_at)` em `click_events`**: o Postgres não indexa automaticamente o lado que referencia a FK.
- **FK `onDelete: Restrict`**: links nunca são apagados, só desativados.
- **Sem IP em `click_events`**: ver `.agents/rules/security.md`.
- **Redirect**: `updateManyAndReturn`, disponível no Prisma desde a 6.2.0 para PostgreSQL, faz o UPDATE atômico com RETURNING sem SQL cru. Se o resultado vier vazio, um `findUnique({ slug })` distingue 404 de 410. O caminho de sucesso usa 1 query. Confirmado na referência do Prisma 7. **Nota:** o Prisma 8 (ainda em RC) renomeia o método para `updateAll()`. Como o projeto fixa o Prisma 7.10.0, nada muda agora; ao subir para o 8, renomear a chamada.
- **Dispositivo guardado só como categoria**: enum `DeviceType { MOBILE, DESKTOP, TABLET, BOT, UNKNOWN }` (`BOT` identificado antes, por `isPreviewBot`; ver "Bots de preview"), classificado no momento do clique por uma função pura do domínio (`ClickTracker`), sem lib. A ordem é:
  1. `Sec-CH-UA-Mobile` (`?1` → `MOBILE`), um Client Hint que só navegadores Chromium enviam;
  2. regex no `User-Agent` (`iPad|Tablet` → `TABLET`; `Mobi|Android|iPhone` → `MOBILE`);
  3. senão `DESKTOP`;
  4. sem UA → `UNKNOWN`.
  
  O UA cru não é persistido (minimização; o UA ajuda em fingerprinting). **Limitação documentada:** desde o iPadOS 13, o Safari do iPad manda UA de Mac, então esses iPads aparecem como `DESKTOP`. Android tablets são detectados. Consequência aceita: o histórico não pode ser reclassificado. Descartados: UA cru com classificação na leitura (duplica a regra no SQL e encarece o `GROUP BY`) e categoria + UA cru com retenção curta (exige job agendado, YAGNI).
- **Referrer guardado só como host normalizado**: `referrer_host text NULL`, em que `null` significa direto/desconhecido. É extraído por uma função pura do domínio: `new URL()`, só `http:`/`https:`, `hostname` em minúsculas e sem `www.`; qualquer outra coisa vira `null`. O parsing já é a sanitização, porque o header é input hostil (*referral spam*) e um hostname tem no máximo 253 caracteres. Ganha-se pouco com mais do que o host: desde ~2021 os navegadores usam `strict-origin-when-cross-origin` por padrão e só mandam a origem entre sites diferentes. Apps nativos (WhatsApp, e-mail) não mandam referrer, então o dashboard precisa explicar o balde "direto/desconhecido". Descartados: URL completa e host+caminho (quase nunca chegam e podem expor PII de terceiros ao criador do link, que é anônimo). Evolução: agrupar por domínio registrável (`l.facebook.com` e `m.facebook.com` → `facebook.com`), o que exige a Public Suffix List.
- **O "dia" das estatísticas é o dia em `America/Sao_Paulo`**, com o rótulo "dias no horário de Brasília" no gráfico: `date_trunc('day', clicked_at AT TIME ZONE 'America/Sao_Paulo')`. Usa o nome IANA, não o offset `-03:00`, para que o banco de fusos absorva uma eventual volta do horário de verão (abolido pelo Decreto 9.772/2019). Descartados:
  - UTC: cliques entre 21h e 23h59 de Brasília cairiam no dia seguinte;
  - agregar por hora em UTC e juntar em dias no cliente: falha em fusos com meia hora e duplica lógica no navegador.
  
  **Evolução documentada:** usar o fuso do navegador de quem vê (`Intl`), enviado por cookie e validado por whitelist com `Intl.supportedValuesOf('timeZone')`. Muda só a query e a entrada, não o schema.

Modelo de dados fechado. Janela de tempo do gráfico: decidir na etapa de rotas.
