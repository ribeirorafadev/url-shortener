# Mapa de erros (aprovado em 2026-09-30)

Parte do contexto de domínio, lido sob demanda pelo índice do `AGENTS.md`. Trechos marcados **[→ spec]** são detalhe de implementação e vão para a spec do MVP quando ela for escrita.

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
| `url` | R4: IPv6 numérico (RC10) | Endereços IPv6 numéricos não são aceitos. Use o nome do site. | domínio |
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
| Upstash indisponível (fail-closed), configuração do Upstash ausente ou inválida (RC4) ou IP ausente (RC5) | Não foi possível criar o link agora. Tente em alguns minutos. | sim |
| Banco lento ou fora (timeout de 5 s) | *(a mesma acima)* | sim |
| Safe Browsing fora do ar, lento (> 2 s), cota esgotada (B1, fail-closed) ou `SAFE_BROWSING_API_KEY` ausente (RC4) | Não foi possível criar o link agora. Tente em alguns minutos. | sim |
| Origem canônica não resolvida (RC2, fail-fast) | *(a mesma acima)* | sim, como erro |
| 3 colisões de slug seguidas | *(a mesma acima)* | sim, como erro |
| Erro inesperado | Algo deu errado. Tente novamente. | sim |

**Página de gestão e `deactivateLink`:**

| Situação | Resposta |
|---|---|
| Token fora do formato (43 caracteres base64url) | `404`, sem consultar o banco (mesma ideia da pré-validação do slug) |
| Token no formato, mas inexistente | `404`, a mesma página (não revela "quase acerto") |
| Banco fora ao abrir a página | Página "Serviço indisponível. Tente novamente em instantes." |
| Origem canônica não resolvida (RC2), necessária para o QR | A mesma página, com log como erro |
| `deactivateLink` com token inválido | Não foi possível desativar: link não encontrado. |
| `deactivateLink` em link já desativado | Sucesso: Link desativado. (idempotente) |
| `deactivateLink` com banco fora | Não foi possível desativar agora. Tente em alguns minutos. |

A página de gestão **não tem rate limit**, de propósito: adivinhar um token de 256 bits é inviável, e o limite só gastaria a cota do Upstash.
