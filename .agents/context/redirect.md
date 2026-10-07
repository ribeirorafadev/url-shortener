# Redirect

Parte do contexto de domínio, lido sob demanda pelo índice do `AGENTS.md`. Trechos marcados **[→ spec]** são detalhe de implementação e vão para a spec do MVP quando ela for escrita.

## Regras

- **Pré-validação do formato do slug (decidida em 2026-09-29):** a primeira coisa que o `GET`/`HEAD /[slug]` faz é chamar `isValidSlugFormat(slug)`, uma função pura do domínio que testa `^[A-Za-z0-9]{7}$` **[→ spec]**. É a mesma regra de alfabeto e tamanho do `SlugGenerator`, definida num lugar só. Fora do formato → `404` imediato, **antes do rate limit e do banco**. Pedido malformado (`/wp-login.php`, `/.env`, `/admin`) nunca vira link, então não gasta a cota do Upstash nem uma consulta. Descartados: rate limit antes do formato (gasta a cota com lixo) e sem checagem (gasta a cota e uma consulta ao banco).
  - **Rota fixa na raiz (B-4, aprovado em 2026-10-07):** nenhuma rota fixa na raiz tem exatamente 7 caracteres `[A-Za-z0-9]`, porque esconderia o slug igual (ex.: uma página de privacidade seria `/privacidade`, não `/privacy`). Hoje só existe `/manage`, com 6.
- **Respostas do redirect**:
  - `302 Found` + `Cache-Control: no-store` quando o link está ativo;
  - `404 Not Found` quando o slug não existe;
  - `410 Gone` quando o link existe mas expirou, esgotou o limite ou foi desativado.
  - `429 Too Many Requests` + `Retry-After` quando o IP passa do rate limit (ver `.agents/rules/security-rate-limit.md`).
  - `503 Service Unavailable` + `Retry-After` quando o banco não responde em 5 s (`connectionTimeoutMillis`, ver `.agents/rules/architecture-persistence.md`) ou falha. O texto é fixo: "Serviço indisponível. Tente novamente em instantes." O erro é logado com o slug, nunca com o destino. Na criação, o mesmo caso vira o estado `error` com "Não foi possível criar o link agora. Tente em alguns minutos."
  - **Corpo das respostas sem redirect (decidido em 2026-09-29):** o `404`, o `410` e a página neutra dos bots (`200`) levam um **HTML mínimo em pt-BR gerado no próprio Route Handler**: título, uma frase, CSS inline e um link "criar um novo link". Um único módulo de templates, na camada de entrada, gera essas três páginas e também as de `429` e `503`. **Os templates não têm `<script>` e não interpolam input do visitante**, só textos e status nossos (RC6; ver `.agents/rules/security-core.md`).
    - O **texto é fixo**, e nenhum dado do link (slug, destino) é interpolado no HTML, o que elimina XSS por construção.
    - Headers: `Content-Type: text/html; charset=utf-8` e `Cache-Control: no-store`.
    - **O `410` mostra o motivo, com um texto fixo por caso** (decidido em 2026-09-29): "Este link foi desativado por quem o criou.", "Este link expirou." ou "Este link atingiu o limite de acessos.". Sem data nem número de acessos, para manter "nada do link no HTML". Se mais de um motivo valer, a precedência é **desativado → expirado → esgotado**, porque a ação explícita do criador vem primeiro. O domínio devolve o motivo como tipo discriminado (ex.: `'deactivated' | 'expired' | 'exhausted'`). Descartados: mensagem genérica (a pessoa que clicou não sabe o que fazer) e motivo com detalhes (expõe escolhas do criador sem ganho).
    - Motivo: o redirect é um `route.ts`, que devolve uma `Response` crua, e uma página React não consegue responder `410`.
    - Descartados: texto puro (parece app quebrado para quem avalia o portfólio) e redirect para uma página React (`302 → 200`), que deixaria de responder `410`/`404` de verdade e violaria o critério de "pronto" do PRD.
- **Parâmetros no link curto são ignorados (P2, decidido em 2026-09-30):** em `/aB3xZ9k?utm_source=instagram`, o que vem depois do `?` é descartado, e o `Location` é sempre o `destination_url` gravado, sem nada anexado. Motivo: o destino é imutável (PRD), e repassar parâmetros deixaria **qualquer pessoa**, sem o token, alterar o destino. Ex.: `?next=https://evil.com` explorando um *open redirect* do site de destino com a credibilidade do link legítimo. Também poderia estourar os 2048 caracteres da R5. Para marketing, o caminho é **um link por canal**, com as UTMs já no destino: cada canal ganha estatísticas próprias no dashboard. Descartados: repassar tudo e repassar só `utm_*` (sujaria o analytics do dono e exigiria mesclar parâmetros e revalidar o tamanho).
- **Por que 302 e não 301**: o 301 é cacheado pelo navegador. A partir do segundo clique, o navegador vai direto ao destino sem passar pelo servidor, e o sistema perde o analytics e o controle de expiração e desativação.
- **Incremento atômico**: a checagem de desativação, de limite e de expiração e o incremento do contador acontecem numa única operação no banco. Com a checagem separada do incremento, dois cliques simultâneos com o contador em 99 (limite 100) passariam os dois. **[→ spec]** A forma de referência é esta (a implementação exata via Prisma fica para a spec):

  ```sql
  UPDATE links
  SET click_count = click_count + 1
  WHERE slug = $1
    AND deactivated_at IS NULL
    AND (max_clicks IS NULL OR click_count < max_clicks)
    AND (expires_at IS NULL OR expires_at > now())
  RETURNING id, destination_url;
  ```

  Corrigido em 2026-09-30: a versão anterior **não checava `deactivated_at`**, então um link desativado continuaria redirecionando. Ela também usava o nome de coluna `original_url`, diferente do schema (`destination_url`), e não devolvia o `id`, que o `after()` precisa para gravar o evento.

  Se zero linhas forem afetadas, o link não existe ou está inativo. É preciso distinguir os dois casos para responder 404 ou 410.
- **Registro detalhado do clique** (dispositivo, referrer): fica fora do caminho crítico do redirect, gravado depois que a resposta sai (decidido em 2026-09-29). O mecanismo é o **`after()` de `next/server`**, que funciona em Route Handler e, na Vercel, usa o `waitUntil` da plataforma para manter a função viva até o fim do callback. Esse prazo é o `maxDuration` da rota: 300 s no Hobby com Fluid compute. Um "fire and forget" comum poderia ser interrompido quando a função termina.
  - **Os headers são lidos e classificados antes do `after()`** (`ClickTracker`, função pura). O callback recebe só valores prontos (`linkId`, `deviceType`, `referrerHost`) e apenas grava.
  - **Se a gravação falhar**, o visitante não percebe, porque o 302 já saiu. O Next registra o erro com `console.error`, sem retry. O nosso log leva o slug, **nunca a URL de destino**, que pode conter dado privado. O resultado é a divergência aceita em `data-model.md` (`click_count` duplicado).
  - Descartados: gravar antes de responder, porque uma falha na tabela de eventos viraria erro para o visitante e o analytics derrubaria o link; e UPDATE + INSERT numa única query (CTE), que exige SQL escrito à mão e tem o mesmo problema. Evolução: fila com retry (ex.: QStash), se a perda de eventos passar a importar.

## Bots de preview de link (decidido)

Quando um link curto é colado no WhatsApp, Slack, Telegram, X, Facebook, LinkedIn ou Discord, o bot do app faz um `GET` na URL, segue o `302` e lê as meta tags Open Graph do destino para montar o card de prévia. Sem tratamento, o bot infla a contagem de cliques e consome o limite: um link de uso único seria gasto antes de o destinatário clicar.

**Regra:**

- **Link sem limite** (`max_clicks` nulo): todos recebem o `302`, e o preview mostra o destino. O acesso de bot **não incrementa** o `click_count`.
- **Link com limite**: o bot recebe um `200` com uma página neutra, com meta OG genéricas ("Link de acesso limitado · abra para continuar"), **sem revelar o destino e sem consumir nada**. Isso anula o bypass por UA forjado (`curl -A "WhatsApp/2.0"`): quem finge ser bot recebe a página neutra, nunca o destino.
- **Registro:** o acesso de bot vira evento com `device_type = BOT`, sem coluna nova. O dashboard mostra "pré-visualizado N× por bots" à parte e **exclui `BOT` dos totais**. O `click_count` nunca é incrementado por bot.
  - **Só link ativo gera evento (RC9, decidido em 2026-10-07):** o evento de bot é gravado só quando o link está ativo (302 ou página neutra). `404` e `410` **nunca** geram evento, nem de humano nem de bot: o desligamento é o fim da história do link. Descartado: gravar acesso de bot a link inativo (dados sobre um link que já não funciona).
- **Detecção:** lista própria no domínio (`isPreviewBot(userAgent)`, função pura com regex, testada com UAs reais), cobrindo `WhatsApp/`, `Slackbot`, `facebookexternalhit`, `Twitterbot`, `TelegramBot`, `LinkedInBot` e `Discordbot`. Os padrões vêm da documentação de cada plataforma. **Sem falso positivo (B-3, aprovado em 2026-10-07):** cada padrão é casado na forma mais específica documentada: ancorado no início quando o UA começa com o nome (`^WhatsApp/`), ou como token com barra quando o nome vem dentro do UA (`Discordbot/`). Os testes incluem UAs de navegadores embutidos de apps (Facebook, Instagram), que continuam humanos; senão, um humano num link com limite receberia a página neutra. A lib `isbot` foi descartada por ser dependência nova para um problema que cerca de 8 padrões resolvem.
- **Limitação documentada:** scanners de segurança de e-mail (Defender Safe Links, Proofpoint, Mimecast) abrem links com UA de navegador comum e continuam consumindo links limitados. A raiz está na RFC 9110, §9.2.1: `GET` é método seguro, e consumir um link num GET é mudança de estado.
- **Requisições `HEAD` (decidido em 2026-09-29):** recebem o mesmo tratamento de um bot de preview. Um handler `HEAD` próprio só lê o link: sem limite → `302` com `Location`; com limite → `200` sem revelar o destino; inexistente → `404`; inativo → `410`. **Não incrementa `click_count` nem gera evento.** O handler próprio é obrigatório porque, sem ele, o Next 16 responde o `HEAD` executando o `GET` (`auto-implement-methods.ts`), e um verificador de links gastaria um link de uso único. Base: RFC 9110, §9.2.1 (`HEAD` é seguro) e §9.1 (servidor de uso geral deve suportar `GET` e `HEAD`). Descartados: o padrão do Next (consome o link) e o `405` (verificadores de link passariam a acusar o link como quebrado).

**Evolução documentada:** uma página de confirmação para links com limite. O `GET` mostra um botão, e só o `POST` (Server Action) consome o link e redireciona. Resolve também os scanners de e-mail e respeita a semântica de "GET seguro". O custo é um clique a mais para o humano.

## Fluxo

**Redirecionar** (caminho mais quente, com leituras ~100× mais frequentes que escritas). Route Handler `src/app/[slug]/route.ts`, que exporta `GET` e `HEAD`. A ordem dos passos é regra; os nomes de método no esboço (`findUnique`, `updateManyAndReturn`) são **[→ spec]**:
   ```
   1. isValidSlugFormat(slug) falhou → 404 (sem Upstash nem banco)
   2. rate limit por IP (/64 no IPv6) → 429 se exceder; Upstash fora ou lento (>1 s), configuração ausente (RC4) ou IP ausente (RC5) → segue (fail-open)
   3. HEAD ou isPreviewBot(UA)?
      ├─ sim → só lê (findUnique): 404 | 410 com motivo | com limite → 200 página neutra | sem limite → 302 sem incrementar
      └─ não → updateManyAndReturn (atômico)
               ├─ 1 linha → 302 + Cache-Control: no-store
               └─ vazio  → findUnique: 404 ou 410 com motivo
   4. after(): grava o evento de clique só com o link ativo (BOT para bot de preview; nada para HEAD, 404 ou 410)
   banco sem resposta em 5 s ou com falha, em qualquer passo → 503
   ```
