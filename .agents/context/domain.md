# Domínio — short-url

Glossário, regras de negócio e fluxos já decididos. O schema de dados está **fechado** (a consolidar na spec): ver "Modelo de dados" no fim do arquivo.

## Glossário

- **Link**: registro que associa um slug a uma URL de destino. Tem limite de cliques e data de expiração, ambos opcionais.
- **Slug**: identificador público e curto do link, a parte que vai na URL (`/aB3xZ9k`).
- **URL de destino**: para onde o visitante é redirecionado. Só `http`/`https`.
- **Token de gestão**: segredo longo e aleatório, gerado na criação e exibido uma única vez. Quem o possui pode ver as estatísticas e desativar aquele link (`/manage/[token]`). Nunca é exposto publicamente.
- **Evento de clique**: registro de um redirecionamento bem-sucedido, com dispositivo, referrer e data/hora.
- **Link ativo / inativo**: é inativo se foi desativado, se passou da data de expiração ou se atingiu o limite de cliques. Um link inativo não redireciona.

## Regras de negócio

- **Slug**: 7 caracteres base62, gerados com CSPRNG (ex.: `crypto.getRandomValues`, nativo), o que dá ~3,5 × 10¹² combinações. Tem constraint `UNIQUE` no banco e, se houver colisão, gera outro. Nunca sequencial, para impedir enumeração.
  - **Colisão (decidida em 2026-09-30): até 3 tentativas.** A colisão é detectada **na gravação**: o `INSERT` falha pelo `UNIQUE` (erro `P2002` do Prisma), e o repositório traduz isso num erro do domínio. Nunca "consultar e depois gravar", que tem race condition entre as duas etapas. O `LinkService` sorteia de novo, até 3 vezes no total.
  - Três colisões seguidas (~1 em 10¹⁹ com 1 milhão de links) não são azar, são sinal de defeito (ex.: gerador quebrado). Nesse caso a criação devolve erro genérico e **loga como erro**.
  - Descartados: sem nova tentativa (usuário veria erro por azar, 1 em 3,5 milhões com 1 milhão de links) e loop sem limite (um bug viraria função travada martelando o banco até o timeout).
- **Validação da URL de destino** (decidida em 2026-09-28). Fica numa função pura do domínio (`UrlValidator`). A análise usa o `new URL()` nativo (WHATWG), e as regras valem **sobre o resultado da análise, não sobre o texto**. A borda só barra entrada vazia ou maior que o limite antes de chamar o domínio.
  - **`trim()` em todos os campos de texto do formulário (P4, decidido em 2026-09-30),** na camada de entrada, antes de qualquer checagem (inclusive a do vazio e a R6). O `String.prototype.trim` nativo (ECMAScript) remove espaço, tab, quebra de linha e espaço não separável (U+00A0) **só nas pontas**. Sem isso, `" exemplo.com"` viraria `"https:// exemplo.com"` na R6 e daria "URL inválida" sem motivo visível. Também vale para o limite de cliques: `"10 "` passa a ser aceito como `10`. Espaço **no meio** da URL não é removido, porque pode ser proposital (o parser o converte para `%20`). Descartados: não tratar (erro confuso após colar do WhatsApp/Word) e remover espaços internos (mudaria o destino sem avisar).
  - **R1.** Protocolo só `http:`/`https:`. Rejeita `javascript:`, `data:`, `file:` e outros.
    - `http:` continua aceito (decidido em 2026-09-28), mas a tela de criação mostra o **aviso** "este destino não usa conexão segura" quando o protocolo final for `http:`. Motivos para não exigir só HTTPS: o ganho contra phishing é nulo (sites de phishing usam HTTPS com certificado grátis); o Chrome 154 (outubro de 2026) já avisa antes de abrir site público em HTTP; e o servidor não acessa o destino, então não pode promover `http` para `https` sem risco de gerar link quebrado.
  - **R2.** Sem usuário e senha na URL. Rejeita `https://nubank.com.br@evil.com/login`, em que o `hostname` real é `evil.com` e o resto é tratado como usuário (truque de phishing).
  - **R3.** O destino não pode ser o nosso próprio domínio. Encadear links curtos esconde o destino final e permite loop (A → B → A). O domínio próprio chega por configuração, injetada no construtor.
  - **R4.** O host tem que ser público. Rejeita `localhost`, loopback, IPs privados, link-local e hosts sem ponto (`http://intranet`). O servidor nunca acessa o destino, então não há SSRF; o risco é o link mandar o navegador da vítima para a rede interna dela, como o painel do roteador (CSRF contra roteadores domésticos).
  - **R5.** No máximo **2048 caracteres**, medidos na URL normalizada (`url.href`). Cobre URLs reais (UTM, URLs pré-assinadas) e mantém o header `Location` do 302 bem abaixo dos buffers de 4 a 8 KB de proxies comuns. Descartado: 8000, o mínimo que a RFC 9110, §4.1, recomenda suportar, porque um `Location` desse tamanho pode estourar o buffer de um proxy corporativo e virar 502 para o visitante.
  - **R6.** Entrada sem protocolo recebe `https://` na frente (`exemplo.com/promo` → `https://exemplo.com/promo`), e o resultado passa por todas as regras. `localhost:3000` continua rejeitada, porque o parser lê `localhost:` como protocolo e ela cai na R1.
  - **R7. A URL não pode estar na blocklist do Google Safe Browsing (incluída no MVP em 2026-09-30).** É checada **só na criação**, depois de R1 a R6 passarem. O redirect não faz consulta externa.
    - **Porta do domínio:** a interface `UrlThreatChecker` (ex.: `check(url): Promise<'safe' | 'dangerous'>`) é injetada no construtor do `LinkService`, como o `LinkRepository`. O domínio não sabe que é o Google. Os testes usam um fake em memória.
    - **Adaptador:** Safe Browsing **v5, modo "No-Storage Real-Time", endpoint `hashes.search`**. O adaptador canonicaliza a URL conforme a spec do Google, gera as expressões de host e caminho, calcula o SHA-256 de cada uma e envia **só prefixos de 4 bytes**; depois compara localmente os hashes completos que voltam. **A URL nunca sai do servidor**, o que é coerente com o `security.md` (URLs de destino podem conter dados privados). Sem cache local obrigatório. Usa `fetch` e `crypto.subtle` nativos, **sem dependência nova**.
    - **Termos:** uso gratuito e **não comercial** (doc "Appropriate Usage"). Ao avisar o usuário, é obrigatório atribuir: "Advisory provided by Google", com link para o Safe Browsing Advisory.
    - Descartados:
      - `urls.search`, que envia a URL inteira e ainda é `v5alpha1`;
      - Google Web Risk, que envia a URL inteira e é voltado a uso comercial com faturamento;
      - URLhaus, que foca em malware, não em phishing, e exige Auth-Key.
    - **Limitações:** só pega o que o Google já conhece (golpe recém-criado passa). Um site que vira golpe depois da criação não é pego; a reverificação periódica é evolução (PRD).
    - **Serviço indisponível (B1, decidido em 2026-09-30): fail-closed.** Se o Google não responder em **2 s**, der erro ou a cota tiver acabado, a criação é recusada com "Não foi possível criar o link agora. Tente em alguns minutos.", e a falha é logada (sem a API key). Motivo: com fail-open, um atacante poderia **esgotar a cota de propósito** e desligar a proteção quando quisesse. O redirect nunca consulta o Google, então os links existentes não são afetados. É coerente com a criação fail-closed do rate limit (10a). Descartado: fail-open (criar sem checar).
    - **Onde fica o adaptador (B2, decidido em 2026-09-30):** `src/infra/safe-browsing-url-threat-checker.ts`, na pasta nova de integrações externas (ver `architecture.md`). `src/data/` continua só com o banco.
    - **Mensagem de bloqueio (B3, decidida em 2026-09-30).** Aparece embaixo do campo `url`:
      > ⚠ Este endereço é suspeito de golpe (phishing) ou de distribuir vírus e não pode ser encurtado. A checagem do Google pode errar; se o site é seu e é seguro, você pode pedir revisão ao Google.
      > Advisory provided by Google ← link para `https://developers.google.com/safe-browsing/v4/advisory`
      - Exigências do Google (doc "Appropriate Usage", seção "User warnings"), que não são escolha nossa:
        - **não afirmar certeza**: usar termos como "suspeito", "possível" ou "provável";
        - a **atribuição "Advisory provided by Google" com link** para o Safe Browsing Advisory;
        - o **README** deve avisar sobre falsos positivos e falsos negativos (ver PRD, critério de "pronto").
      - A atribuição fica **em inglês, com a frase exata**, como um aviso legal: a versão em português da doc é tradução automática. Não se usa o tipo de ameaça no texto.
      - Contrato: o estado de erro da `createLink` ganha `threatAdvisory?: true`, para a tela desenhar a linha do Google com o link (o `fieldErrors` só carrega texto).
      - Descartados: atribuição traduzida ("Aviso fornecido pelo Google", arrisca descumprir os termos) e texto por tipo de ameaça (trabalho extra e detalhe útil sobretudo ao golpista).
  - Fora de escopo (PRD): bloqueio de outros encurtadores e reverificação periódica dos links já criados.
  - **Domínios internacionalizados (IDN) e ataque homógrafo (P6, decidido em 2026-09-30): aceitos, com limitação documentada.** O `new URL()` converte o host para punycode (`аpple.com` com "а" cirílico → `xn--pple-43d.com`). O navegador de quem clica denuncia o disfarce: o Chrome exibe punycode quando detecta mistura de alfabetos ou um domínio inteiro de letras sósias (doc "IDN in Google Chrome"). Descartados: recusar mistura de alfabetos, que fica como **evolução** (ganho pequeno, porque o golpe mais comum usa só letras latinas, como `paypa1.com`, que só a blocklist da R7 pode pegar), e aceitar só ASCII, que barraria domínios `.br` legítimos com acento.
- **Limite de cliques e expiração**: opcionais. O padrão é sem limite e sem expiração. São funcionalidades de produto (link de uso único, campanha com prazo), **não** proteção. A proteção é o rate limiting. Os dois podem ser combinados. Regras decididas em 2026-09-28 (a borda converte as strings do `FormData` em tipos, e o `LinkService` valida):
  - **Limite de cliques:** inteiro entre **1 e 1.000.000**, com conversão estrita (`/^\d+$/` antes do `Number()`), então `"10abc"`, `"1e3"`, `"-5"` e `"2.5"` são rejeitados. O teto evita que um valor acima do `int` do Postgres (2.147.483.647) vire erro 500 em vez de erro de validação, e 1 milhão cobre qualquer campanha realista.
  - **Expiração:** o usuário escolhe uma **duração pronta** (1 h, 24 h, 7 dias ou 30 dias, e o servidor calcula `agora + duração`) **ou "até o fim do dia X"**, com um seletor só de data. Esse dia é interpretado em `America/Sao_Paulo`, o mesmo conceito de "dia" do dashboard: "fim do dia 30/10" vira `2026-10-30T23:59:59.999-03:00`.
    - A conversão não usa biblioteca: o offset vem do `Intl.DateTimeFormat` com `timeZone: 'America/Sao_Paulo'` e `timeZoneName: 'longOffset'`, que respeita a base IANA (devolve `GMT-02:00` para dezembro de 2018, ainda com horário de verão). O Node 24 não tem a API `Temporal`.
    - Mínimo: a data tem que ser hoje ou depois, no horário de Brasília. Máximo: **5 anos**, só como trava de sanidade (o máximo de um `Date` em JS é o ano 275760). Um limite de produto não faria sentido, porque o link sem expiração é permitido.
    - Descartados: data e hora livres com `datetime-local`, porque o valor chega sem fuso (`"2026-10-30T23:59"`) e o criador e o servidor podem estar em fusos diferentes; e só durações prontas, que não cobrem "campanha até o dia 30".
- **Pré-validação do formato do slug (decidida em 2026-09-29):** a primeira coisa que o `GET`/`HEAD /[slug]` faz é chamar `isValidSlugFormat(slug)`, uma função pura do domínio que testa `^[A-Za-z0-9]{7}$`. É a mesma regra de alfabeto e tamanho do `SlugGenerator`, definida num lugar só. Fora do formato → `404` imediato, **antes do rate limit e do banco**. Pedido malformado (`/wp-login.php`, `/.env`, `/admin`) nunca vira link, então não gasta a cota do Upstash nem uma consulta. Descartados: rate limit antes do formato (gasta a cota com lixo) e sem checagem (gasta a cota e uma consulta ao banco).
- **Respostas do redirect**:
  - `302 Found` + `Cache-Control: no-store` quando o link está ativo;
  - `404 Not Found` quando o slug não existe;
  - `410 Gone` quando o link existe mas expirou, esgotou o limite ou foi desativado.
  - `429 Too Many Requests` + `Retry-After` quando o IP passa do rate limit (ver `security.md`, "Números do rate limit").
  - `503 Service Unavailable` + `Retry-After` quando o banco não responde em 5 s (`connectionTimeoutMillis`, ver `architecture.md`) ou falha. O texto é fixo: "Serviço indisponível. Tente novamente em instantes." O erro é logado com o slug, nunca com o destino. Na criação, o mesmo caso vira o estado `error` com "Não foi possível criar o link agora. Tente em alguns minutos."
  - **Corpo das respostas sem redirect (decidido em 2026-09-29):** o `404`, o `410` e a página neutra dos bots (`200`) levam um **HTML mínimo em pt-BR gerado no próprio Route Handler**: título, uma frase, CSS inline e um link "criar um novo link". Um único módulo de templates, na camada de entrada, gera essas três páginas e também as de `429` e `503`.
    - O **texto é fixo**, e nenhum dado do link (slug, destino) é interpolado no HTML, o que elimina XSS por construção.
    - Headers: `Content-Type: text/html; charset=utf-8` e `Cache-Control: no-store`.
    - **O `410` mostra o motivo, com um texto fixo por caso** (decidido em 2026-09-29): "Este link foi desativado por quem o criou.", "Este link expirou." ou "Este link atingiu o limite de acessos.". Sem data nem número de acessos, para manter "nada do link no HTML". Se mais de um motivo valer, a precedência é **desativado → expirado → esgotado**, porque a ação explícita do criador vem primeiro. O domínio devolve o motivo como tipo discriminado (ex.: `'deactivated' | 'expired' | 'exhausted'`). Descartados: mensagem genérica (a pessoa que clicou não sabe o que fazer) e motivo com detalhes (expõe escolhas do criador sem ganho).
    - Motivo: o redirect é um `route.ts`, que devolve uma `Response` crua, e uma página React não consegue responder `410`.
    - Descartados: texto puro (parece app quebrado para quem avalia o portfólio) e redirect para uma página React (`302 → 200`), que deixaria de responder `410`/`404` de verdade e violaria o critério de "pronto" do PRD.
- **Parâmetros no link curto são ignorados (P2, decidido em 2026-09-30):** em `/aB3xZ9k?utm_source=instagram`, o que vem depois do `?` é descartado, e o `Location` é sempre o `destination_url` gravado, sem nada anexado. Motivo: o destino é imutável (PRD), e repassar parâmetros deixaria **qualquer pessoa**, sem o token, alterar o destino. Ex.: `?next=https://evil.com` explorando um *open redirect* do site de destino com a credibilidade do link legítimo. Também poderia estourar os 2048 caracteres da R5. Para marketing, o caminho é **um link por canal**, com as UTMs já no destino: cada canal ganha estatísticas próprias no dashboard. Descartados: repassar tudo e repassar só `utm_*` (sujaria o analytics do dono e exigiria mesclar parâmetros e revalidar o tamanho).
- **Por que 302 e não 301**: o 301 é cacheado pelo navegador. A partir do segundo clique, o navegador vai direto ao destino sem passar pelo servidor, e o sistema perde o analytics e o controle de expiração e desativação.
- **Incremento atômico**: a checagem de desativação, de limite e de expiração e o incremento do contador acontecem numa única operação no banco. Com a checagem separada do incremento, dois cliques simultâneos com o contador em 99 (limite 100) passariam os dois. A forma de referência é esta (a implementação exata via Prisma fica para a spec):

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
  - **Se a gravação falhar**, o visitante não percebe, porque o 302 já saiu. O Next registra o erro com `console.error`, sem retry. O nosso log leva o slug, **nunca a URL de destino**, que pode conter dado privado. O resultado é a divergência aceita em "Modelo de dados" (`click_count` duplicado).
  - Descartados: gravar antes de responder, porque uma falha na tabela de eventos viraria erro para o visitante e o analytics derrubaria o link; e UPDATE + INSERT numa única query (CTE), que exige SQL escrito à mão e tem o mesmo problema. Evolução: fila com retry (ex.: QStash), se a perda de eventos passar a importar.
- **Token de gestão**: exibido só na resposta de criação. Se o usuário perder o link de gestão, não há recuperação (não existe conta).
  - **Formato:** 32 bytes de `crypto.getRandomValues` em **base64url sem padding** (RFC 4648, §5), com 43 caracteres seguros para URL.
  - **Exibição única (decidida em 2026-09-28):** a Server Action devolve o resultado como estado (`useActionState`), e um **card na própria tela de criação** mostra o link curto, o link de gestão, o QR, os botões "copiar" e "baixar" e o aviso "guarde este link: não há recuperação". Um F5 descarta o estado, o que é o comportamento certo para um segredo exibido uma vez. Nada do token vai para `localStorage`, cookie ou log. Descartado: redirecionar para `/manage/[token]` logo após criar, porque isso gravaria o token no histórico do navegador na hora (ver `security.md`, "Vazamentos do token").
- **Contrato da `createLink`:** Server Action não tem status HTTP de erro (é sempre `POST 200`). O resultado é um tipo discriminado:

  ```ts
  type CreateLinkState =
    | { status: 'idle' }
    | { status: 'success'; shortUrl: string; manageUrl: string; qrCodeDataUrl: string | null; isInsecureDestination: boolean }
    | { status: 'error'; fieldErrors?: Partial<Record<'url' | 'maxClicks' | 'expiration', string>>; message?: string; threatAdvisory?: true }
  ```

  `shortUrl` e `manageUrl` são absolutos (`https://<domínio>/...`). `isInsecureDestination` alimenta o aviso de destino `http:` (R1). O mapeamento completo de erros está em "Mapa de erros", no fim do arquivo.
  - **Perda do token depois de criado (P5, decidido em 2026-09-30).** Há dois caminhos:
    - **Aba fechada sem guardar o link de gestão (comum): mitigado com duas medidas.**
      - **C:** o link de gestão aparece em destaque no card (borda de alerta, acima do link curto), junto com o aviso "guarde este link: não há recuperação".
      - **B:** enquanto o link de gestão **não foi copiado**, um `beforeunload` pede confirmação ao fechar ou recarregar a aba. Depois de copiar, o evento é removido.
      - Limitações (MDN, `beforeunload`): o texto da caixa é genérico do navegador, o evento exige interação prévia com a página e **não é confiável em celular**. Por isso a C cobre o celular.
    - **Resposta perdida na rede depois de gravar (raro): limitação documentada.** O servidor não sabe que a resposta se perdeu, e sem conta não há como reenviar o token. O link órfão é inofensivo, porque ninguém conhece o slug nem o token.
    - Descartado: só o aviso de texto.
  - **Duplo envio (P3, decidido em 2026-09-30):** o botão "Encurtar" fica desabilitado, com o texto "Encurtando…", enquanto a action está em andamento (`isPending` do `useActionState`). Isso evita o segundo link órfão do duplo clique. Requisição forjada repetida fica a cargo do rate limit (10b). Descartados: não tratar (duplo clique cria 2 links e 1 órfão) e chave de idempotência no servidor (infraestrutura extra contra algo que o rate limit já segura).
  - **Depois de gravar, a criação nunca responde erro (P1, decidido em 2026-09-30).** O token é exibido uma vez só e é insubstituível, então uma falha posterior à gravação (hoje, só a geração do QR) vira sucesso **parcial**: `qrCodeDataUrl: null`, e o card mostra os dois links com o aviso "Não foi possível gerar o QR code". A falha é logada. O banco não muda nada, porque o QR nunca é persistido (é gerado sob demanda a partir da URL curta).
  - Descartados: devolver erro, que faz o usuário perder o token e deixa um link órfão; e gerar o QR antes de gravar, que obrigaria a partir a criação do domínio em duas chamadas ou a fazer o domínio conhecer o QR (AD-004).
- **QR code:** PNG em data URL, com **512 px** (`qrcode.toDataURL`), exibido num `<img>` com botão "baixar". PNG funciona em qualquer lugar (WhatsApp, Word, gráfica). SVG foi descartado porque a exibição inline exigiria `dangerouslySetInnerHTML`. ⚠️ O `qrcode@1.5.4` (último release em 08/2024) traz `yargs@15`, usado só pela CLI dele: reavaliar o peso das dependências transitivas na spec.

## Bots de preview de link (decidido)

Quando um link curto é colado no WhatsApp, Slack, Telegram, X, Facebook, LinkedIn ou Discord, o bot do app faz um `GET` na URL, segue o `302` e lê as meta tags Open Graph do destino para montar o card de prévia. Sem tratamento, o bot infla a contagem de cliques e consome o limite: um link de uso único seria gasto antes de o destinatário clicar.

**Regra:**

- **Link sem limite** (`max_clicks` nulo): todos recebem o `302`, e o preview mostra o destino. O acesso de bot **não incrementa** o `click_count`.
- **Link com limite**: o bot recebe um `200` com uma página neutra, com meta OG genéricas ("Link de acesso limitado · abra para continuar"), **sem revelar o destino e sem consumir nada**. Isso anula o bypass por UA forjado (`curl -A "WhatsApp/2.0"`): quem finge ser bot recebe a página neutra, nunca o destino.
- **Registro:** o acesso de bot vira evento com `device_type = BOT`, sem coluna nova. O dashboard mostra "pré-visualizado N× por bots" à parte e **exclui `BOT` dos totais**. O `click_count` nunca é incrementado por bot.
- **Detecção:** lista própria no domínio (`isPreviewBot(userAgent)`, função pura com regex, testada com UAs reais), cobrindo `WhatsApp/`, `Slackbot`, `facebookexternalhit`, `Twitterbot`, `TelegramBot`, `LinkedInBot` e `Discordbot`. Os padrões vêm da documentação de cada plataforma. A lib `isbot` foi descartada por ser dependência nova para um problema que cerca de 8 padrões resolvem.
- **Limitação documentada:** scanners de segurança de e-mail (Defender Safe Links, Proofpoint, Mimecast) abrem links com UA de navegador comum e continuam consumindo links limitados. A raiz está na RFC 9110, §9.2.1: `GET` é método seguro, e consumir um link num GET é mudança de estado.
- **Requisições `HEAD` (decidido em 2026-09-29):** recebem o mesmo tratamento de um bot de preview. Um handler `HEAD` próprio só lê o link: sem limite → `302` com `Location`; com limite → `200` sem revelar o destino; inexistente → `404`; inativo → `410`. **Não incrementa `click_count` nem gera evento.** O handler próprio é obrigatório porque, sem ele, o Next 16 responde o `HEAD` executando o `GET` (`auto-implement-methods.ts`), e um verificador de links gastaria um link de uso único. Base: RFC 9110, §9.2.1 (`HEAD` é seguro) e §9.1 (servidor de uso geral deve suportar `GET` e `HEAD`). Descartados: o padrão do Next (consome o link) e o `405` (verificadores de link passariam a acusar o link como quebrado).

**Evolução documentada:** uma página de confirmação para links com limite. O `GET` mostra um botão, e só o `POST` (Server Action) consome o link e redireciona. Resolve também os scanners de e-mail e respeita a semântica de "GET seguro". O custo é um clique a mais para o humano.

## Fluxos

1. **Criar link**: formulário → Server Action → rate limit (10/min e 100/dia por IP; Upstash fora → erro, fail-closed) → validação da URL (R1 a R6) → R7: consulta o Google Safe Browsing (só prefixos de hash) → gera slug e token → grava via Prisma (colisão de slug → sorteia de novo, até 3 tentativas) → o domínio devolve o link curto e o token → a Server Action gera o QR code (camada de entrada) → devolve o estado `success` com o link curto, o link de gestão e o QR, exibidos uma única vez no card de resultado.
2. **Redirecionar** (caminho mais quente, com leituras ~100× mais frequentes que escritas). Route Handler `src/app/[slug]/route.ts`, que exporta `GET` e `HEAD`:
   ```
   1. isValidSlugFormat(slug) falhou → 404 (sem Upstash nem banco)
   2. rate limit por IP (/64 no IPv6) → 429 se exceder; Upstash fora ou lento (>1 s) → segue (fail-open)
   3. HEAD ou isPreviewBot(UA)?
      ├─ sim → só lê (findUnique): 404 | 410 com motivo | com limite → 200 página neutra | sem limite → 302 sem incrementar
      └─ não → updateManyAndReturn (atômico)
               ├─ 1 linha → 302 + Cache-Control: no-store
               └─ vazio  → findUnique: 404 ou 410 com motivo
   4. after(): grava o evento de clique (BOT para bot de preview; nada para HEAD)
   banco sem resposta em 5 s ou com falha, em qualquer passo → 503
   ```
3. **Gerenciar**: `GET /manage/[token]` → busca o link pelo token (nunca pelo slug) → agrega os cliques no Postgres (totais de toda a vida por dispositivo e referrer; gráfico diário dos últimos 30 dias) → dashboard renderizado no servidor, com o QR code da URL curta (gerado na hora), `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex` e `Cache-Control: no-store` → desativação via Server Action.

## Modelo de dados (fechado; consolidar na spec)

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

Modelo de dados fechado.

## Página de gestão (`/manage/[token]`)

- **Janela do gráfico diário (decidida em 2026-09-29): últimos 30 dias, ou desde a criação se o link for mais novo.** O gráfico fica sempre legível (no máximo 30 barras), e a consulta tem custo fixo, coberta pelo índice `(link_id, clicked_at)`. Os **totais** (cliques, por dispositivo e por referrer) cobrem **toda a vida do link**; só o gráfico tem janela. Descartados: desde a criação (centenas de barras em links antigos e uma consulta que cresce com a idade) e seletor de 7/30/90 dias, que fica como **evolução** (acrescentar depois não muda o banco; exige whitelist no `?dias=`).
- **Desativação irreversível, com confirmação (decidida em 2026-09-29):** o botão "Desativar" abre um passo de confirmação na própria página ("Tem certeza? Não dá para desfazer" → "Sim, desativar"). Não existe `reactivateLink`. Motivo: o PRD limita o impacto de um token vazado a "ver e desativar, nunca sequestrar". Com reativação, quem roubasse o token poderia religar um link que o dono desligou de propósito (ex.: documento privado compartilhado por engano). Descartados: reversível (amplia o poder do token vazado) e um clique só, sem confirmação (um clique errado perde o link para sempre, inclusive QR impresso).
- **`deactivateLink` idempotente (decidida em 2026-09-29):** desativar um link já desativado responde **sucesso** e **mantém a data original** de `deactivated_at`. O banco roda `UPDATE … SET deactivated_at = now() WHERE manage_token_hash = $1 AND deactivated_at IS NULL`. Se nenhuma linha for afetada, uma busca pelo hash distingue "token inválido" (erro) de "já desativado" (sucesso). Base: idempotência, RFC 9110, §9.2.2. Descartados: erro "já estava desativado" (o objetivo do usuário já foi cumprido) e sobrescrever a data (ela deixaria de dizer quando o link foi desligado de fato).
  - **Regra fixa:** a action identifica o link **pelo token (hash)**, nunca pelo slug ou pelo id. O slug é público, então desativar por slug seria IDOR (OWASP API Security Top 10, API1:2023, *Broken Object Level Authorization*). A proteção CSRF é a embutida do Next (ver `security.md`).
- **QR code também na página de gestão (P1b, decidido em 2026-09-30):** a página mostra o QR da URL curta com o botão "Baixar", gerado no servidor pela mesma função da criação (512 px, PNG em data URL, não persistido). Ela é o lugar de recuperar o QR: quando a geração falhou na criação (P1) ou quando o usuário perdeu a imagem baixada. Descartados: não oferecer recuperação (dependeria de um gerador externo) e botão "tentar de novo" no card (só vale enquanto o card estiver aberto, e exigiria uma action que aceitasse apenas URLs nossas para não virar gerador de QR público).
- **Token no path e headers da página (decidido em 2026-09-29):** o token continua em `/manage/[token]`. A resposta leva `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex` e `Cache-Control: no-store`. O tratamento de cada canal de vazamento (Referer, logs da Vercel, histórico) e as alternativas descartadas estão em `security.md`, "Vazamentos do token".

## Mapa de erros (aprovado em 2026-09-30)

Princípio: mensagem clara para o usuário, **nenhum detalhe interno** (stack trace, nome de tabela, "Prisma"). Erro inesperado vira mensagem genérica mais log, sem token nem URL de destino.

**`createLink`: erros por campo (`fieldErrors`)**, exibidos embaixo do campo:

| Campo | Situação | Mensagem | Onde |
|---|---|---|---|
| `url` | vazio | Informe a URL de destino. | entrada |
| `url` | mais de 2048 caracteres | A URL pode ter no máximo 2048 caracteres. | entrada e domínio (R5) |
| `url` | não é URL | Isso não parece uma URL válida. Ex.: https://exemplo.com | domínio |
| `url` | R1: protocolo proibido | Só são aceitos links http:// ou https://. | domínio |
| `url` | R2: usuário e senha na URL | Links com usuário e senha embutidos não são aceitos. | domínio |
| `url` | R3: próprio domínio | Não é possível encurtar um link deste próprio encurtador. | domínio |
| `url` | R4: host não público | O destino precisa ser um site público. | domínio |
| `url` | R7: listada no Safe Browsing | Este endereço é suspeito de golpe (phishing) ou de distribuir vírus e não pode ser encurtado. A checagem do Google pode errar; se o site é seu e é seguro, você pode pedir revisão ao Google. + linha "Advisory provided by Google" com link (`threatAdvisory: true`) | domínio (via `UrlThreatChecker`) |
| `maxClicks` | não é inteiro (`10abc`, `2.5`, `-5`, `1e3`) | Informe um número inteiro, sem letras ou casas decimais. | entrada |
| `maxClicks` | fora de 1 a 1.000.000 | O limite deve ficar entre 1 e 1.000.000 cliques. | domínio |
| `expiration` | data inválida (`2026-02-30`) | Data inválida. | entrada |
| `expiration` | data no passado (Brasília) | A data precisa ser hoje ou depois. | domínio |
| `expiration` | mais de 5 anos | A data pode ser no máximo daqui a 5 anos. | domínio |
| `expiration` | duração fora da lista (requisição forjada) | Escolha uma das opções de duração. | entrada |
| `expiration` | duração e data juntas (requisição forjada) | Escolha uma duração ou uma data, não as duas. | entrada |

`maxClicks` e `expiration` vazios significam "sem limite" e "sem expiração", não erro. O destino `http:` gera **aviso**, não erro (`isInsecureDestination`).

**`createLink`: erros gerais (`message`)**, exibidos acima do formulário:

| Situação | Mensagem | Log |
|---|---|---|
| Rate limit por minuto | Muitas tentativas. Aguarde um minuto. | não |
| Rate limit diário | Você atingiu o limite de links por hoje. Tente amanhã. | não |
| Upstash indisponível (fail-closed) | Não foi possível criar o link agora. Tente em alguns minutos. | sim |
| Banco lento ou fora (timeout de 5 s) | *(a mesma acima)* | sim |
| Safe Browsing fora do ar, lento (> 2 s) ou cota esgotada (B1, fail-closed) | Não foi possível criar o link agora. Tente em alguns minutos. | sim |
| 3 colisões de slug seguidas | *(a mesma acima)* | sim, como erro |
| Erro inesperado | Algo deu errado. Tente novamente. | sim |

**Página de gestão e `deactivateLink`:**

| Situação | Resposta |
|---|---|
| Token fora do formato (43 caracteres base64url) | `404`, sem consultar o banco (mesma ideia da pré-validação do slug) |
| Token no formato, mas inexistente | `404`, a mesma página (não revela "quase acerto") |
| Banco fora ao abrir a página | Página "Serviço indisponível. Tente novamente em instantes." |
| `deactivateLink` com token inválido | Não foi possível desativar: link não encontrado. |
| `deactivateLink` em link já desativado | Sucesso: Link desativado. (idempotente) |
| `deactivateLink` com banco fora | Não foi possível desativar agora. Tente em alguns minutos. |

A página de gestão **não tem rate limit**, de propósito: adivinhar um token de 256 bits é inviável, e o limite só gastaria a cota do Upstash.
