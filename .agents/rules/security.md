# Segurança — short-url

## Superfície de risco
- Autenticação/autorização: sem login (AD-003). A autorização sobre um link é a posse do **token de gestão**: longo, aleatório (CSPRNG) e exibido uma única vez. O token é uma credencial: nunca aparece em URL pública, log, analytics ou resposta de redirect. **Exceção documentada:** os logs de requisição da própria Vercel registram o path `/manage/<token>` (ver "Vazamentos do token"). O código da aplicação continua proibido de logar o token.
- Dados sensíveis manipulados:
  - o token de gestão;
  - as URLs de destino, que podem carregar dados privados em query string;
  - os metadados de clique (user-agent, referrer);
  - o IP do visitante, usado como chave de rate limit. IP é dado pessoal pela LGPD.
- Dependências externas críticas: Neon (Postgres), Upstash (Redis de rate limit), Vercel (hosting e edge) e Google Safe Browsing (blocklist da R7, só na criação).

## Ameaças consideradas e mitigação
- **DDoS volumétrico**: tratado pela proteção de infraestrutura da edge da Vercel, antes de o tráfego chegar às funções. Não é problema do código da aplicação.
- **Abuso funcional** (criação de links em massa, inflar cliques): rate limit por IP na camada de entrada, antes do domínio e do banco.
- **Phishing e redirect malicioso**: a URL de destino é validada pelas regras R1 a R7 de `domain.md`. Só aceita `http:`/`https:`; rejeita credenciais embutidas (`https://banco.com@evil.com`), o próprio domínio (encadeamento e loop) e hosts não públicos (localhost e IPs privados, contra CSRF na rede interna do visitante); limita o tamanho a 2048 caracteres. **R7:** recusa URLs listadas no Google Safe Browsing (ver "Blocklist"). O link pode ser desativado.
- **Enumeração de links**: slug aleatório via CSPRNG, nunca sequencial.
- **SQL injection**: acesso só via Prisma, sem concatenação.
- **Race condition no limite de cliques**: checagem e incremento numa única operação atômica.
- **Consumo de link com limite por quem não é o destinatário**: bots de preview e requisições `HEAD` só leem o link, sem incrementar, e nunca veem o destino de um link com limite (`domain.md`, "Bots de preview" e "Requisições `HEAD`"). Scanners de e-mail com UA de navegador continuam sendo uma limitação documentada.
- **Varredura de caminhos** (`/wp-login.php`, `/.env`): o slug fora do formato recebe `404` antes do rate limit e do banco (`domain.md`, "Pré-validação do formato do slug").
- **CSRF nas Server Actions** (`createLink`, `deactivateLink`): proteção embutida do Next.js, verificada na documentação da v16 (`data-security.mdx`, `action-handler.ts`). Server Actions só aceitam `POST`, e o Next compara o header `Origin` com o `Host`/`X-Forwarded-Host`, abortando a action se forem diferentes. Sem `serverActions.allowedOrigins`, só a mesma origem é aceita. **Não configurar `allowedOrigins`.**

## Política
- Todo input externo é hostil até prova em contrário. O formato é validado na borda (entrada), e as regras de negócio são revalidadas no domínio.
- Segredos (`DATABASE_URL` e `DIRECT_URL`, as duas connection strings do Neon, os tokens do Upstash e a `SAFE_BROWSING_API_KEY`) só via variáveis de ambiente (Vercel em produção, `.env.local` em dev). Nunca hardcoded nem commitados: o `.gitignore` ignora `.env*`, exceto `.env.example`.
- O **`.npmrc` do projeto é versionado**, porque guarda as regras de supply chain, e por isso **nunca pode conter token de registry** (`//registry.npmjs.org/:_authToken=`). Credenciais do npm ficam só no `~/.npmrc` do usuário.
- **Artefatos de teste são ignorados** (`test-results/`, `playwright-report/`, `.playwright-mcp/`): screenshots e traces do fluxo de gestão podem conter a URL com o token.
- Nenhum `catch` silencioso. Erros esperados (URL inválida, link inexistente ou expirado) viram resposta HTTP explícita; os inesperados são logados sem vazar token nem segredo.

## Decidido na sessão de design
- **Token de gestão guardado só como hash SHA-256** (coluna `BYTEA` de 32 bytes com `UNIQUE`). O token tem 32 bytes de CSPRNG (256 bits), então um hash rápido basta: inverter o hash é inviável, e a busca continua indexada. Hash lento (argon2/bcrypt) foi descartado porque protege segredos de baixa entropia, não é indexável (obrigaria o padrão seletor+verificador) e custa de 100 a 250 ms de CPU por acesso sem ganho real. Plaintext foi descartado porque um dump do banco daria controle de todos os links. Hash via Web Crypto (`crypto.subtle.digest`), sem dependência nova. Detalhamento e alternativas vão para a spec.
- **Formato e exibição do token:** base64url sem padding (43 caracteres), exibido uma única vez no card de resultado da criação. Nunca vai para `localStorage`, cookie, log ou redirect (ver `domain.md`, "Token de gestão").
- **O IP do visitante não é persistido** em `click_events`, nem em claro nem como hash. Base: LGPD, art. 6º, III (necessidade), e o MVP não usa o IP para nada (geolocalização e visitantes únicos estão fora de escopo). Também evita que a ferramenta vire um "IP logger", já que qualquer pessoa cria link sem login. O IP só existe efêmero: na chave de rate limit do Upstash (com TTL) e nos logs da Vercel.
  - O Marco Civil (Lei 12.965/2014, art. 15), que obriga a guardar registros de acesso por 6 meses, só vale para pessoa jurídica com fins econômicos. Não se aplica a projeto pessoal; reavaliar se o produto virar empresa.
  - Hash simples de IP foi descartado porque o IPv4 tem só 2³² valores, então é reversível por força bruta. Se um dia for preciso contar visitantes únicos, o caminho é `hash(salt_diário + IP + user-agent)` com o salt apagado a cada 24 h, como faz o Plausible. É mudança barata: coluna nova, só para os cliques daí em diante.

## Vazamentos do token que o hash não cobre (decidido em 2026-09-29)
O hash só protege o token **no banco**. O token **continua no path** (`/manage/[token]`), e cada canal de vazamento tem um tratamento explícito:
- **Header `Referer`: mitigado.** A página de gestão responde com `Referrer-Policy: no-referrer`, e o navegador nunca envia a URL com o token a outro site. Ela também leva `X-Robots-Tag: noindex` (para não ser indexada se o link vazar) e `Cache-Control: no-store`.
- **Logs de requisição da Vercel: risco aceito.** O log de runtime mostra o path acessado, com o token. Só o dono do projeto vê esse log, e ele já controla o banco, então o log não dá a ninguém um acesso novo. O plano Hobby guarda os logs por **1 hora** (documentação de Runtime Logs da Vercel, verificada em 2026-09-29).
- **Histórico do navegador: risco residual aceito.** *Mitigado em parte (2026-09-28):* a criação exibe o token num card, sem redirecionar para `/manage/[token]`, então ele só entra no histórico quando o usuário abre o link de gestão. O que sobra só importa em computador compartilhado.
- Descartados:
  - **token no fragmento** (`/manage#<token>`, que o navegador não envia ao servidor, RFC 3986, §3.5): fecharia o log, mas obriga a renderizar o dashboard no navegador (JavaScript lê o `#` e busca os dados por `POST`), e não resolve o histórico;
  - **campo "cole seu token"** sem token na URL: fecha os três canais, mas o usuário perde o link clicável e precisa guardar 43 caracteres.

## Números do rate limit (decididos em 2026-09-29)
- **Criação:** **10 por minuto e 100 por dia** por IP. São dois limitadores, e os dois precisam aprovar. O teto diário é a defesa real contra spam de phishing: um robô cria no máximo 100 links por dia por IP. O limite por minuto segura rajadas.
- **Redirect:** **300 por minuto** por IP. É folgado de propósito, porque um IP pode ser muita gente: CGNAT das operadoras de celular, rede de empresa. A intenção é frear robôs, não pessoas. O limite de cliques de cada link continua garantido pelo UPDATE atômico, e não pelo rate limit.
- **Algoritmo:** janela deslizante (`Ratelimit.slidingWindow`), que conta os pedidos do IP nos últimos 60 s ou 24 h.
- **Timeout da lib:** **1 s** (o padrão é 5 s). Passou disso, vale "Rate limiter indisponível".
- **IP:** lido com `ipAddress(request)` de `@vercel/functions`. A Vercel sobrescreve o `x-forwarded-for`, então o visitante não consegue forjar o IP (doc "Request headers" da Vercel).
- **Chave do rate limit no IPv6 (decidida em 2026-09-30): o prefixo `/64`**, ou seja, os 4 primeiros grupos (`2804:14c:5b80:9a10::/64`).
  - Motivo: os últimos 64 bits são o identificador de interface, escolhido pelo próprio aparelho (RFC 4291, §2.5.1), e os sistemas trocam esse pedaço periodicamente (endereços temporários, RFC 8981). Com o endereço completo como chave, um robô trocaria o fim a cada pedido e nunca atingiria o limite. O `/64` identifica a conexão (casa ou aparelho), como o IPv4 faz hoje.
  - IPv4 é usado como está. IPv4 mapeado em IPv6 (`::ffff:177.10.20.30`) é tratado como IPv4.
  - A normalização é uma **função pura sem biblioteca**, com testes de tabela: expande o `::`, trata maiúsculas e minúsculas e o formato mapeado.
  - Descartados: endereço completo (rate limit inútil contra IPv6) e `/48`, que pode juntar clientes diferentes de uma operadora no mesmo contador.
- **Resposta ao exceder:**
  - redirect: `429 Too Many Requests` com `Retry-After` (RFC 6585, §4), no mesmo estilo de HTML fixo do 404/410;
  - criação: estado `error` com "Muitas tentativas. Aguarde um minuto." (ou "…tente amanhã", se o teto diário estourou).
- Os números ficam em **constantes num lugar só** da camada de entrada.
- **Cota:** o Upstash Free tem 500 mil comandos por mês (~16 mil por dia), e cada checagem gasta pelo menos 1. Se a cota esgotar, vale "Rate limiter indisponível".
- Descartados: rigoroso (5/min na criação e 30/min no redirect), que bloquearia um grupo de colegas atrás do mesmo IP; e folgado (60/min na criação e 3.000/min no redirect), que deixaria um robô criar ~86 mil links por dia por IP.

## Rate limiter indisponível (decidido em 2026-09-29)
Vale para Upstash fora do ar, erro de rede, cota esgotada ou timeout. O comportamento **muda conforme a rota**:
- **Redirect (`GET`/`HEAD /[slug]`): fail-open.** A requisição passa sem rate limit. Um componente de proteção não pode derrubar o produto: os links já distribuídos, inclusive QR impresso, continuam abrindo. O abuso possível durante a queda é inflar cliques. O limite de cliques continua garantido pelo UPDATE atômico no banco, e o DDoS volumétrico fica com a edge da Vercel.
- **Criação (`createLink`): fail-closed.** Devolve o estado `error` com `message` do tipo "Não foi possível criar o link agora. Tente em alguns minutos." Liberar a criação sem limite, numa ferramenta sem login, abriria a porta para spam de links de phishing, e quem quer criar pode tentar de novo depois.
- A falha é **logada** (sem IP em claro nem token), nunca engolida.
- A lib `@upstash/ratelimit` já deixa passar por padrão quando o Upstash demora (`timeout`, padrão de **5 s**, com `reason: "timeout"`; doc "Features › Timeout"). Por isso:
  - o timeout é **reduzido** (valor na decisão dos números), para o redirect não ficar parado esperando;
  - na criação, `reason === "timeout"` é tratado como falha (fail-closed).
- Descartados: fail-open nos dois (spam de criação durante a queda) e fail-closed nos dois (todos os links param por causa do Upstash).

## Blocklist: Google Safe Browsing (R7, incluída no MVP em 2026-09-30)
Regra de negócio em `domain.md` (R7). Aqui ficam os aspectos de segurança, privacidade e custo, verificados na documentação do Google em 2026-09-30:
- **Privacidade:** o adaptador usa o `hashes.search` da v5 e envia **só prefixos de 4 bytes do SHA-256**, nunca a URL. A comparação final é feita no nosso servidor. É a mesma política de minimização aplicada ao IP (LGPD, art. 6º, III).
- **Custo:** gratuito. "All use of Safe Browsing APIs is free of charge" (doc "Pricing") e "There is no cost for use of this API" (doc "Usage Restrictions"). Os termos são de **uso não comercial**; se o produto virar comercial, migrar para o Google Web Risk (mesma porta do domínio, só troca o adaptador).
- **Cota:** a documentação **não publica o número**. A cota padrão aparece no Google Cloud Console depois de ativar a API, e dá para pedir aumento sem custo. Fontes de terceiros citam 10 mil consultas por dia (não é número oficial). O consumo esperado é baixo: só a criação consulta, e ela já é limitada a 100 por dia por IP (10b).
- **Configuração (feita pelo Rafael):** conta Google → projeto no Google Cloud Console → criar a API key → ativar a "Safe Browsing API" (doc "Get started"). O passo a passo não pede conta de faturamento.
- **API key:**
  - só no servidor, via variável de ambiente `SAFE_BROWSING_API_KEY` (nunca no cliente nem em `NEXT_PUBLIC_*`);
  - **restrita no console à Safe Browsing API**, para uma chave vazada não servir para outras APIs do projeto;
  - vai na query string da chamada ao Google (`?key=`), então **nunca logar a URL da requisição** ao Google.
- **Pendentes:**
  - B1: serviço fora do ar ou cota esgotada (fail-open ou fail-closed);
  - B2: pasta do adaptador;
  - B3: mensagem de bloqueio com a atribuição obrigatória "Advisory provided by Google".
