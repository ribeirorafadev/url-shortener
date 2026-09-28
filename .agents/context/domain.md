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
- **Validação da URL de destino** (decidida em 2026-09-28). Fica numa função pura do domínio (`UrlValidator`). A análise usa o `new URL()` nativo (WHATWG), e as regras valem **sobre o resultado da análise, não sobre o texto**. A borda só barra entrada vazia ou maior que o limite antes de chamar o domínio.
  - **R1.** Protocolo só `http:`/`https:`. Rejeita `javascript:`, `data:`, `file:` e outros.
    - `http:` continua aceito (decidido em 2026-09-28), mas a tela de criação mostra o **aviso** "este destino não usa conexão segura" quando o protocolo final for `http:`. Motivos para não exigir só HTTPS: o ganho contra phishing é nulo (sites de phishing usam HTTPS com certificado grátis); o Chrome 154 (outubro de 2026) já avisa antes de abrir site público em HTTP; e o servidor não acessa o destino, então não pode promover `http` para `https` sem risco de gerar link quebrado.
  - **R2.** Sem usuário e senha na URL. Rejeita `https://nubank.com.br@evil.com/login`, em que o `hostname` real é `evil.com` e o resto é tratado como usuário (truque de phishing).
  - **R3.** O destino não pode ser o nosso próprio domínio. Encadear links curtos esconde o destino final e permite loop (A → B → A). O domínio próprio chega por configuração, injetada no construtor.
  - **R4.** O host tem que ser público. Rejeita `localhost`, loopback, IPs privados, link-local e hosts sem ponto (`http://intranet`). O servidor nunca acessa o destino, então não há SSRF; o risco é o link mandar o navegador da vítima para a rede interna dela, como o painel do roteador (CSRF contra roteadores domésticos).
  - **R5.** No máximo **2048 caracteres**, medidos na URL normalizada (`url.href`). Cobre URLs reais (UTM, URLs pré-assinadas) e mantém o header `Location` do 302 bem abaixo dos buffers de 4 a 8 KB de proxies comuns. Descartado: 8000, o mínimo que a RFC 9110, §4.1, recomenda suportar, porque um `Location` desse tamanho pode estourar o buffer de um proxy corporativo e virar 502 para o visitante.
  - **R6.** Entrada sem protocolo recebe `https://` na frente (`exemplo.com/promo` → `https://exemplo.com/promo`), e o resultado passa por todas as regras. `localhost:3000` continua rejeitada, porque o parser lê `localhost:` como protocolo e ela cai na R1.
  - Fora de escopo (PRD): blocklist de URLs maliciosas e bloqueio de outros encurtadores.
- **Limite de cliques e expiração**: opcionais. O padrão é sem limite e sem expiração. São funcionalidades de produto (link de uso único, campanha com prazo), **não** proteção. A proteção é o rate limiting. Os dois podem ser combinados. Regras decididas em 2026-09-28 (a borda converte as strings do `FormData` em tipos, e o `LinkService` valida):
  - **Limite de cliques:** inteiro entre **1 e 1.000.000**, com conversão estrita (`/^\d+$/` antes do `Number()`), então `"10abc"`, `"1e3"`, `"-5"` e `"2.5"` são rejeitados. O teto evita que um valor acima do `int` do Postgres (2.147.483.647) vire erro 500 em vez de erro de validação, e 1 milhão cobre qualquer campanha realista.
  - **Expiração:** o usuário escolhe uma **duração pronta** (1 h, 24 h, 7 dias ou 30 dias, e o servidor calcula `agora + duração`) **ou "até o fim do dia X"**, com um seletor só de data. Esse dia é interpretado em `America/Sao_Paulo`, o mesmo conceito de "dia" do dashboard: "fim do dia 30/10" vira `2026-10-30T23:59:59.999-03:00`.
    - A conversão não usa biblioteca: o offset vem do `Intl.DateTimeFormat` com `timeZone: 'America/Sao_Paulo'` e `timeZoneName: 'longOffset'`, que respeita a base IANA (devolve `GMT-02:00` para dezembro de 2018, ainda com horário de verão). O Node 24 não tem a API `Temporal`.
    - Mínimo: a data tem que ser hoje ou depois, no horário de Brasília. Máximo: **5 anos**, só como trava de sanidade (o máximo de um `Date` em JS é o ano 275760). Um limite de produto não faria sentido, porque o link sem expiração é permitido.
    - Descartados: data e hora livres com `datetime-local`, porque o valor chega sem fuso (`"2026-10-30T23:59"`) e o criador e o servidor podem estar em fusos diferentes; e só durações prontas, que não cobrem "campanha até o dia 30".
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
  - **Formato:** 32 bytes de `crypto.getRandomValues` em **base64url sem padding** (RFC 4648, §5), com 43 caracteres seguros para URL.
  - **Exibição única (decidida em 2026-09-28):** a Server Action devolve o resultado como estado (`useActionState`), e um **card na própria tela de criação** mostra o link curto, o link de gestão, o QR, os botões "copiar" e "baixar" e o aviso "guarde este link: não há recuperação". Um F5 descarta o estado, o que é o comportamento certo para um segredo exibido uma vez. Nada do token vai para `localStorage`, cookie ou log. Descartado: redirecionar para `/manage/[token]` logo após criar, porque isso gravaria o token no histórico do navegador na hora (ver `security.md`, "Pendente de mitigação").
- **Contrato da `createLink`:** Server Action não tem status HTTP de erro (é sempre `POST 200`). O resultado é um tipo discriminado:

  ```ts
  type CreateLinkState =
    | { status: 'idle' }
    | { status: 'success'; shortUrl: string; manageUrl: string; qrCodeDataUrl: string; isInsecureDestination: boolean }
    | { status: 'error'; fieldErrors?: Partial<Record<'url' | 'maxClicks' | 'expiration', string>>; message?: string }
  ```

  `shortUrl` e `manageUrl` são absolutos (`https://<domínio>/...`). `isInsecureDestination` alimenta o aviso de destino `http:` (R1). O mapeamento completo de erros fica para a etapa de tratamento de erros.
- **QR code:** PNG em data URL, com **512 px** (`qrcode.toDataURL`), exibido num `<img>` com botão "baixar". PNG funciona em qualquer lugar (WhatsApp, Word, gráfica). SVG foi descartado porque a exibição inline exigiria `dangerouslySetInnerHTML`. ⚠️ O `qrcode@1.5.4` (último release em 08/2024) traz `yargs@15`, usado só pela CLI dele: reavaliar o peso das dependências transitivas na spec.

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

1. **Criar link**: formulário → Server Action → rate limit → validação da URL → gera slug e token → grava via Prisma → o domínio devolve o link curto e o token → a Server Action gera o QR code (camada de entrada) → devolve o estado `success` com o link curto, o link de gestão e o QR, exibidos uma única vez no card de resultado.
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
