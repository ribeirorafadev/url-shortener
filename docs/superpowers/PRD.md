# short-url — PRD (Product Requirements Document)

Documento de intenção de produto — estável, revisado no lugar (não é log append-only como o `ADR.md`). Escopo de projeto, não de feature: decisões por feature ficam em `specs/*-design.md`.

## Problema

São dois problemas, nesta ordem de prioridade:

1. **Portfólio.** O GitHub do autor ([ribeirorafadev](https://github.com/ribeirorafadev)) ainda não tem nenhum projeto full-stack ou backend. Os dois projetos seguintes do roadmap (gestão de acessos/IAM e CRM) serão em Java/Spring Boot. Este precisa provar capacidade full-stack em **Node.js/TypeScript**, para diversificar a stack mostrada, e ficar pronto rápido.
2. **Produto.** Links longos são ruins de compartilhar, e quem compartilha não sabe quantas pessoas clicaram, de onde vieram nem em que dispositivo. Links de campanha, convite ou uso único precisam poder expirar ou ter limite de uso.

O produto precisa funcionar de verdade, com deploy público: um encurtador de URL de fachada não serve como portfólio. O domínio é reconhecível em segundos por quem avalia, e a densidade de engenharia está nos detalhes (geração de slug, redirecionamento no caminho crítico, incremento atômico, rate limiting em serverless, camadas).

## Público-alvo

- **Principal: quem avalia o portfólio.** Recrutadores e avaliadores técnicos de vagas full-stack, que leem o repositório e abrem a demo. O README, o diagrama de system design e o deploy público fazem parte do produto.
- **Usuário final da ferramenta:** qualquer pessoa que queira encurtar um link sem criar conta.

## Escopo do MVP

- Encurtar uma URL e receber um link curto (slug aleatório), um link de gestão secreto (exibido uma única vez) e um QR code.
- Opções na criação, ambas opcionais: **limite de cliques** e **data de expiração**. O padrão é sem limite e sem expiração.
- Redirecionamento rápido (HTTP 302), registrando o clique com dispositivo, referrer e data.
- Página de gestão (`/manage/[token]`) com estatísticas agregadas por dispositivo, referrer e dia, o QR code do link para baixar de novo e a opção de desativar o link.
- Rate limiting na criação e no redirecionamento.
- Validação da URL de destino: só `http`/`https`, mais as regras R2 a R6 de `domain.md`.
- **Checagem de URL maliciosa na criação (R7)**, contra a blocklist do Google Safe Browsing (incluída no MVP em 2026-09-30). Protege quem clica e o próprio domínio da demo, que poderia ser marcado como perigoso se redirecionasse para golpes.
- **Idioma: pt-BR** na interface e no README, porque o alvo atual do portfólio são vagas no Brasil (decidido em 2026-09-28). É coerente com o fuso fixo em `America/Sao_Paulo` e com os textos já definidos (rótulo do gráfico, card neutro para bots). Os identificadores de código ficam em inglês.

## Fora de escopo

- Contas de usuário e login (ver AD-003).
- Cache de redirecionamento e Redis para analytics (YAGNI no volume de portfólio). O README documenta isso como evolução em "como escalaria".
- Agregação ou retenção de eventos de clique antigos (evolução documentada).
- Geolocalização de cliques (país/cidade). O analytics do MVP cobre dispositivo, referrer e data.
- **Reverificação periódica** dos links já criados contra a blocklist (evolução documentada). O MVP checa só na criação; um site que vira golpe depois não é pego.
- Recusar domínios com mistura de alfabetos (homógrafos, P6): evolução documentada.
- Funcionalidades em tempo real (WebSocket).
- **Internacionalização (i18n).** O App Router não tem i18n embutido: o caminho oficial é um segmento `app/[lang]/` mais um redirect no `proxy.ts`. Aqui, o `[lang]` colidiria com o `[slug]` na raiz, e o redirect de idioma acrescentaria um salto ao redirect do link curto, que é o caminho mais quente. Se o alvo passar a incluir vagas internacionais, reavaliar começando pelo README, que não tem custo no código.
- API pública para terceiros: a API existe só para servir a própria aplicação (premissa do AD-001).
- **Alias personalizado** (o usuário escolhe o slug). É evolução documentada no README. Motivos: numa ferramenta anônima, o alias amplifica phishing por squatting de marca (`/nubank`, `/login`), disputa o espaço de nomes com as rotas da aplicação, inclusive as futuras, e é enumerável por definição. Adicionar depois é barato: `slug` já é `text` com `UNIQUE`, sem migration de tipo. Remover depois de lançado quebraria links. Se entrar um dia, exige ASCII estrito `[a-z0-9-]`, normalização para minúsculas (com `UNIQUE` sobre `lower(slug)`), lista de palavras reservadas e uma estratégia contra squatting.
- **Editar a URL de destino.** No MVP o destino é **imutável**: para corrigir, o usuário desativa o link e cria outro. Motivos:
  - evita bait-and-switch, em que o link ganha confiança e depois é trocado para phishing;
  - mantém baixo o impacto de um token vazado (ver e desativar, nunca sequestrar o link);
  - mantém o analytics coerente.
  
  A evolução documentada é o destino **editável só até o primeiro clique** (`UPDATE ... WHERE click_count = 0`, atômico), que serve para corrigir erro de digitação antes de compartilhar sem abrir bait-and-switch. Ela não resolve QR code impresso (quem imprime testa escaneando, e o primeiro clique trava o destino). Os bots de preview também podem travar o link. Edição livre fica descartada enquanto o token tiver vazamentos residuais aceitos (logs da Vercel e histórico do navegador; ver `.agents/rules/security.md`, "Vazamentos do token"), e exigiria histórico de destinos.

## Critério de "pronto"

- Deploy público na Vercel, acessível por URL.
- Fluxo completo funcionando: criar → compartilhar → clicar → ver estatísticas → desativar.
- Slug inexistente responde 404. Link expirado, esgotado ou desativado responde 410.
- O limite de cliques é respeitado sob requisições concorrentes (incremento atômico no banco).
- Rate limiting ativo na criação e no redirecionamento.
- URL listada no Google Safe Browsing é recusada na criação, com aviso qualificado ("suspeito") e a atribuição "Advisory provided by Google".
- Testes automatizados da camada de domínio passando (Vitest; ver `architecture.md`), mais o teste de concorrência com Postgres real e os testes HTTP do redirect e da página de gestão.
- CI (GitHub Actions) verde na `main`, e a publicação na Vercel só acontece depois dele (ruleset + Deployment Checks).
- README com descrição, stack, diagrama de system design, link para o ADR, seção "como escalaria", instruções para rodar localmente e para rodar os testes (Node + Docker, sem conta em nenhum serviço), a dica "um link por canal" (UTM no destino, P2) e o **aviso de que a checagem do Google Safe Browsing pode ter falsos positivos e falsos negativos** (exigência dos termos do Google).
- Tudo entregue em cerca de 1 semana de trabalho.
