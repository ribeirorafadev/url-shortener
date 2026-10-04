---
trigger: model_decision
description: "Números do rate limit, chave /64 do IPv6, resposta ao exceder e o comportamento quando o Upstash cai (fail-open no redirect, fail-closed na criação). Ler ao mexer na criação, no redirect ou no rate limit."
---
# Segurança — rate limit

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
  - o timeout é **reduzido** (1 s, ver "Números do rate limit" acima), para o redirect não ficar parado esperando;
  - na criação, `reason === "timeout"` é tratado como falha (fail-closed).
- Descartados: fail-open nos dois (spam de criação durante a queda) e fail-closed nos dois (todos os links param por causa do Upstash).
