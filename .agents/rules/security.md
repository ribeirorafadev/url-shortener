# Segurança — short-url

## Superfície de risco
- Autenticação/autorização: sem login (AD-003). A autorização sobre um link é a posse do **token de gestão**: longo, aleatório (CSPRNG) e exibido uma única vez. O token é uma credencial: nunca aparece em URL pública, log, analytics ou resposta de redirect.
- Dados sensíveis manipulados:
  - o token de gestão;
  - as URLs de destino, que podem carregar dados privados em query string;
  - os metadados de clique (user-agent, referrer);
  - o IP do visitante, usado como chave de rate limit. IP é dado pessoal pela LGPD.
- Dependências externas críticas: Neon (Postgres), Upstash (Redis de rate limit) e Vercel (hosting e edge).

## Ameaças consideradas e mitigação
- **DDoS volumétrico**: tratado pela proteção de infraestrutura da edge da Vercel, antes de o tráfego chegar às funções. Não é problema do código da aplicação.
- **Abuso funcional** (criação de links em massa, inflar cliques): rate limit por IP na camada de entrada, antes do domínio e do banco.
- **Phishing e redirect malicioso**: a URL de destino é validada e só `http:`/`https:` são aceitos (`javascript:`, `data:`, `file:` e outros são rejeitados). O link pode ser desativado.
- **Enumeração de links**: slug aleatório via CSPRNG, nunca sequencial.
- **SQL injection**: acesso só via Prisma, sem concatenação.
- **Race condition no limite de cliques**: checagem e incremento numa única operação atômica.

## Política
- Todo input externo é hostil até prova em contrário. O formato é validado na borda (entrada), e as regras de negócio são revalidadas no domínio.
- Segredos (`DATABASE_URL` e `DIRECT_URL`, as duas connection strings do Neon, e os tokens do Upstash) só via variáveis de ambiente (Vercel em produção, `.env.local` em dev). Nunca hardcoded nem commitados: o `.gitignore` ignora `.env*`, exceto `.env.example`.
- Nenhum `catch` silencioso. Erros esperados (URL inválida, link inexistente ou expirado) viram resposta HTTP explícita; os inesperados são logados sem vazar token nem segredo.

## Decidido na sessão de design
- **Token de gestão guardado só como hash SHA-256** (coluna `BYTEA` de 32 bytes com `UNIQUE`). O token tem 32 bytes de CSPRNG (256 bits), então um hash rápido basta: inverter o hash é inviável, e a busca continua indexada. Hash lento (argon2/bcrypt) foi descartado porque protege segredos de baixa entropia, não é indexável (obrigaria o padrão seletor+verificador) e custa de 100 a 250 ms de CPU por acesso sem ganho real. Plaintext foi descartado porque um dump do banco daria controle de todos os links. Hash via Web Crypto (`crypto.subtle.digest`), sem dependência nova. Detalhamento e alternativas vão para a spec.
- **O IP do visitante não é persistido** em `click_events`, nem em claro nem como hash. Base: LGPD, art. 6º, III (necessidade), e o MVP não usa o IP para nada (geolocalização e visitantes únicos estão fora de escopo). Também evita que a ferramenta vire um "IP logger", já que qualquer pessoa cria link sem login. O IP só existe efêmero: na chave de rate limit do Upstash (com TTL) e nos logs da Vercel.
  - O Marco Civil (Lei 12.965/2014, art. 15), que obriga a guardar registros de acesso por 6 meses, só vale para pessoa jurídica com fins econômicos. Não se aplica a projeto pessoal; reavaliar se o produto virar empresa.
  - Hash simples de IP foi descartado porque o IPv4 tem só 2³² valores, então é reversível por força bruta. Se um dia for preciso contar visitantes únicos, o caminho é `hash(salt_diário + IP + user-agent)` com o salt apagado a cada 24 h, como faz o Plausible. É mudança barata: coluna nova, só para os cliques daí em diante.

## Pendente de mitigação: vazamentos do token que o hash não cobre
O hash só protege o token **no banco**. Como o token vai no path (`/manage/[token]`), ele vaza por outros canais. Mitigar na etapa de rotas ou na spec:
- **Logs de requisição da Vercel**: registram o path completo, com o token.
- **Histórico do navegador**: a URL de gestão fica salva no histórico e na sincronização do navegador.
- **Header `Referer`**: se a página de gestão tiver links ou recursos externos, a URL com o token pode ir no `Referer`. Candidato: `Referrer-Policy: no-referrer` na página de gestão.

## Em aberto (decidir na spec)
- Se o Upstash cair ou a cota acabar, o rate limiter falha aberto (deixa passar) ou fechado (bloqueia)? Possivelmente diferente para criação e redirect. Isso entra na seção de tratamento de erros.

