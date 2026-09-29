# Segurança — short-url

## Superfície de risco
- Autenticação/autorização: sem login (AD-003). A autorização sobre um link é a posse do **token de gestão**: longo, aleatório (CSPRNG) e exibido uma única vez. O token é uma credencial: nunca aparece em URL pública, log, analytics ou resposta de redirect. **Exceção documentada:** os logs de requisição da própria Vercel registram o path `/manage/<token>` (ver "Vazamentos do token"). O código da aplicação continua proibido de logar o token.
- Dados sensíveis manipulados:
  - o token de gestão;
  - as URLs de destino, que podem carregar dados privados em query string;
  - os metadados de clique (user-agent, referrer);
  - o IP do visitante, usado como chave de rate limit. IP é dado pessoal pela LGPD.
- Dependências externas críticas: Neon (Postgres), Upstash (Redis de rate limit) e Vercel (hosting e edge).

## Ameaças consideradas e mitigação
- **DDoS volumétrico**: tratado pela proteção de infraestrutura da edge da Vercel, antes de o tráfego chegar às funções. Não é problema do código da aplicação.
- **Abuso funcional** (criação de links em massa, inflar cliques): rate limit por IP na camada de entrada, antes do domínio e do banco.
- **Phishing e redirect malicioso**: a URL de destino é validada pelas regras R1 a R6 de `domain.md`. Só aceita `http:`/`https:`; rejeita credenciais embutidas (`https://banco.com@evil.com`), o próprio domínio (encadeamento e loop) e hosts não públicos (localhost e IPs privados, contra CSRF na rede interna do visitante); limita o tamanho a 2048 caracteres. O link pode ser desativado.
- **Enumeração de links**: slug aleatório via CSPRNG, nunca sequencial.
- **SQL injection**: acesso só via Prisma, sem concatenação.
- **Race condition no limite de cliques**: checagem e incremento numa única operação atômica.
- **Consumo de link com limite por quem não é o destinatário**: bots de preview e requisições `HEAD` só leem o link, sem incrementar, e nunca veem o destino de um link com limite (`domain.md`, "Bots de preview" e "Requisições `HEAD`"). Scanners de e-mail com UA de navegador continuam sendo uma limitação documentada.
- **Varredura de caminhos** (`/wp-login.php`, `/.env`): o slug fora do formato recebe `404` antes do rate limit e do banco (`domain.md`, "Pré-validação do formato do slug").
- **CSRF nas Server Actions** (`createLink`, `deactivateLink`): proteção embutida do Next.js, verificada na documentação da v16 (`data-security.mdx`, `action-handler.ts`). Server Actions só aceitam `POST`, e o Next compara o header `Origin` com o `Host`/`X-Forwarded-Host`, abortando a action se forem diferentes. Sem `serverActions.allowedOrigins`, só a mesma origem é aceita. **Não configurar `allowedOrigins`.**

## Política
- Todo input externo é hostil até prova em contrário. O formato é validado na borda (entrada), e as regras de negócio são revalidadas no domínio.
- Segredos (`DATABASE_URL` e `DIRECT_URL`, as duas connection strings do Neon, e os tokens do Upstash) só via variáveis de ambiente (Vercel em produção, `.env.local` em dev). Nunca hardcoded nem commitados: o `.gitignore` ignora `.env*`, exceto `.env.example`.
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

## Em aberto (decidir na spec)
- Se o Upstash cair ou a cota acabar, o rate limiter falha aberto (deixa passar) ou fechado (bloqueia)? Possivelmente diferente para criação e redirect. Isso entra na seção de tratamento de erros.

