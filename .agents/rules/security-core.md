---
trigger: always_on
---
# Segurança — núcleo

## Superfície de risco
- Autenticação/autorização: sem login (AD-003). A autorização sobre um link é a posse do **token de gestão**: longo, aleatório (CSPRNG) e exibido uma única vez. O token é uma credencial: nunca aparece em URL pública, log, analytics ou resposta de redirect. **Exceção documentada:** os logs de requisição da própria Vercel registram o path `/manage/<token>` (ver `security-token.md`, "Vazamentos do token"). O código da aplicação continua proibido de logar o token.
- Dados sensíveis manipulados:
  - o token de gestão;
  - as URLs de destino, que podem carregar dados privados em query string;
  - os metadados de clique (user-agent, referrer);
  - o IP do visitante, usado como chave de rate limit. IP é dado pessoal pela LGPD.
- Dependências externas críticas: Neon (Postgres), Upstash (Redis de rate limit), Vercel (hosting e edge) e Google Safe Browsing (blocklist da R7, só na criação).

## Ameaças consideradas e mitigação
- **DDoS volumétrico**: tratado pela proteção de infraestrutura da edge da Vercel, antes de o tráfego chegar às funções. Não é problema do código da aplicação.
- **Abuso funcional** (criação de links em massa, inflar cliques): rate limit por IP na camada de entrada, antes do domínio e do banco.
- **Phishing e redirect malicioso**: a URL de destino é validada pelas regras R1 a R7 de `.agents/context/url-validation.md`. Só aceita `http:`/`https:`; rejeita credenciais embutidas (`https://banco.com@evil.com`), o próprio domínio (encadeamento e loop) e hosts não públicos (localhost e IPs privados, contra CSRF na rede interna do visitante); limita o tamanho a 2048 caracteres. **R7:** recusa URLs listadas no Google Safe Browsing (ver `security-blocklist.md`). O link pode ser desativado.
- **Enumeração de links**: slug aleatório via CSPRNG, nunca sequencial.
- **SQL injection**: acesso só via Prisma, sem concatenação.
- **Clickjacking, XSS e MIME sniffing (RC6, decidido em 2026-10-07): headers fixos em todas as rotas, no `headers()` do `next.config.ts`.** A CSP é a receita "Without Nonces" da doc do Next 16: `default-src 'self'`, `script-src 'self' 'unsafe-inline'` (o Next injeta scripts inline próprios), `style-src 'self' 'unsafe-inline'`, `img-src 'self' data:` (QR em data URL), `font-src 'self'`, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'`; em dev, `'unsafe-eval'` a mais (a doc exige). Mais `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e `Referrer-Policy: strict-origin-when-cross-origin` (a gestão mantém o `no-referrer`). **[→ spec]** A lista exata.
  - O `frame-ancestors 'none'` fecha o ataque concreto: a página de gestão num `iframe` invisível, induzindo o clique em "Sim, desativar".
  - **Risco aceito:** com `'unsafe-inline'`, um script inline injetado passaria. Exige antes um bug de injeção de HTML, e o app quase não tem por onde: o React escapa o texto, a R1 barra `javascript:`, o referrer vira só host, o slug tem formato validado. Sem login nem cookie de sessão, o pior caso é o token da gestão vazar (ver e desativar, nunca sequestrar). Uma dependência comprometida chega como script `'self'` e passaria por qualquer CSP.
  - **Primeira barreira, reforçada:** lint `react/no-danger` (barra o `dangerouslySetInnerHTML`), e os HTML fixos do redirect não têm `<script>` nem interpolam input (`.agents/context/redirect.md`).
  - HSTS: a Vercel deve enviá-lo nos domínios dela; **conferir com `curl -I` no setup**.
  - Base: Next.js 16, "How to set a Content Security Policy" ("you must use dynamic rendering to add nonces"); MDN, `frame-ancestors`.
  - **Evolução documentada:** CSP com nonce via `proxy.ts`, se o app ganhar login/sessão ou passar a exibir HTML de terceiros. Descartada agora porque o proxy rodaria em toda requisição, inclusive no redirect, e todas as páginas virariam dinâmicas. Também descartados: só headers simples, sem CSP (não barra script de outro domínio), e SRI (experimental no Next).
- **Race condition no limite de cliques**: checagem e incremento numa única operação atômica.
- **Consumo de link com limite por quem não é o destinatário**: bots de preview e requisições `HEAD` só leem o link, sem incrementar, e nunca veem o destino de um link com limite (`.agents/context/redirect.md`, "Bots de preview" e "Requisições `HEAD`"). Scanners de e-mail com UA de navegador continuam sendo uma limitação documentada.
- **Varredura de caminhos** (`/wp-login.php`, `/.env`): o slug fora do formato recebe `404` antes do rate limit e do banco (`.agents/context/redirect.md`, "Pré-validação do formato do slug").
- **CSRF nas Server Actions** (`createLink`, `deactivateLink`): proteção embutida do Next.js, verificada na documentação da v16 (`data-security.mdx`, `action-handler.ts`). Server Actions só aceitam `POST`, e o Next compara o header `Origin` com o `Host`/`X-Forwarded-Host`, abortando a action se forem diferentes. Sem `serverActions.allowedOrigins`, só a mesma origem é aceita. **Não configurar `allowedOrigins`.**

## Política
- Todo input externo é hostil até prova em contrário. O formato é validado na borda (entrada), e as regras de negócio são revalidadas no domínio.
- Segredos (`DATABASE_URL` e `DATABASE_URL_UNPOOLED`, as duas connection strings do Neon, os tokens do Upstash e a `SAFE_BROWSING_API_KEY`) só via variáveis de ambiente (Vercel em produção; na máquina local, `.env.development.local`, ver "Serviços falsos só no `npm run dev`"). Nunca hardcoded nem commitados: o `.gitignore` ignora `.env*`, exceto `.env.example`.
- **Serviços falsos só no `npm run dev` (decidido em 2026-10-01).** A variável `USE_LOCAL_FAKES=true`, no `.env.development.local` (arquivo que só o `next dev` lê e que o Git ignora; decidido em 2026-10-02), troca o Upstash e o Google por falsos locais, para quem clona experimentar o site sem chaves. Duas travas impedem que isso chegue à produção: o ponto de montagem só usa os falsos com `NODE_ENV === 'development'`, e o `next.config.ts` faz o `next build` e o `next start` falharem se a variável estiver ligada. A ausência de uma chave **nunca** ativa um falso: em produção, chave faltando continua sendo fail-closed na criação. Detalhes em `architecture-local-dev.md`.
- **CI sem segredos (decidido em 2026-09-30).** Os testes usam serviços falsos e o Postgres do container, então o GitHub Actions não recebe nenhuma credencial (Neon, Upstash, Google ou Vercel). As ações de terceiros ficam fixadas pelo SHA completo do commit, e o `GITHUB_TOKEN` só tem `contents: read` (GitHub Docs, "Secure use reference"). A senha do Postgres no `compose.yml` é só de desenvolvimento local, com a porta presa ao `127.0.0.1`, e não é segredo.
- **Publicação protegida (decidido em 2026-09-30):** código só chega à produção com o CI verde. São duas travas: o ruleset da `main` e os Deployment Checks da Vercel (ver `architecture-testing-ci.md`).
- O **`.npmrc` do projeto é versionado**, porque guarda as regras de supply chain, e por isso **nunca pode conter token de registry** (`//registry.npmjs.org/:_authToken=`). Credenciais do npm ficam só no `~/.npmrc` do usuário.
- **Artefatos de teste são ignorados** (`test-results/`, `playwright-report/`, `.playwright-mcp/`): screenshots e traces do fluxo de gestão podem conter a URL com o token.
- Nenhum `catch` silencioso. Erros esperados (URL inválida, link inexistente ou expirado) viram resposta HTTP explícita; os inesperados são logados sem vazar token nem segredo.

## IP do visitante (decidido na sessão de design)
- **O IP do visitante não é persistido** em `click_events`, nem em claro nem como hash. Base: LGPD, art. 6º, III (necessidade), e o MVP não usa o IP para nada (geolocalização e visitantes únicos estão fora de escopo). Também evita que a ferramenta vire um "IP logger", já que qualquer pessoa cria link sem login. O IP só existe efêmero: na chave de rate limit do Upstash (com TTL) e nos logs da Vercel.
  - O Marco Civil (Lei 12.965/2014, art. 15), que obriga a guardar registros de acesso por 6 meses, só vale para pessoa jurídica com fins econômicos. Não se aplica a projeto pessoal; reavaliar se o produto virar empresa.
  - Hash simples de IP foi descartado porque o IPv4 tem só 2³² valores, então é reversível por força bruta. Se um dia for preciso contar visitantes únicos, o caminho é `hash(salt_diário + IP + user-agent)` com o salt apagado a cada 24 h, como faz o Plausible. É mudança barata: coluna nova, só para os cliques daí em diante.
