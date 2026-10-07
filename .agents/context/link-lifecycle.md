# Ciclo de vida do link

Parte do contexto de domínio, lido sob demanda pelo índice do `AGENTS.md`. Trechos marcados **[→ spec]** são detalhe de implementação e vão para a spec do MVP quando ela for escrita.

## Slug

- **Slug**: 7 caracteres base62, gerados com CSPRNG (ex.: `crypto.getRandomValues`, nativo), o que dá ~3,5 × 10¹² combinações. Tem constraint `UNIQUE` no banco e, se houver colisão, gera outro. Nunca sequencial, para impedir enumeração.
  - **Colisão (decidida em 2026-09-30): até 3 tentativas.** A colisão é detectada **na gravação**: o `INSERT` falha pelo `UNIQUE` (erro `P2002` do Prisma), e o repositório traduz isso num erro do domínio. Nunca "consultar e depois gravar", que tem race condition entre as duas etapas. O `LinkService` sorteia de novo, até 3 vezes no total.
  - Três colisões seguidas (~1 em 10¹⁹ com 1 milhão de links) não são azar, são sinal de defeito (ex.: gerador quebrado). Nesse caso a criação devolve erro genérico e **loga como erro**.
  - Descartados: sem nova tentativa (usuário veria erro por azar, 1 em 3,5 milhões com 1 milhão de links) e loop sem limite (um bug viraria função travada martelando o banco até o timeout).

## Limite de cliques e expiração

- **Limite de cliques e expiração**: opcionais. O padrão é sem limite e sem expiração. São funcionalidades de produto (link de uso único, campanha com prazo), **não** proteção. A proteção é o rate limiting. Os dois podem ser combinados. Regras decididas em 2026-09-28 (a borda converte as strings do `FormData` em tipos, e o `LinkService` valida):
  - **Limite de cliques:** inteiro entre **1 e 1.000.000**, com conversão estrita (`/^\d+$/` antes do `Number()`), então `"10abc"`, `"1e3"`, `"-5"` e `"2.5"` são rejeitados. O teto evita que um valor acima do `int` do Postgres (2.147.483.647) vire erro 500 em vez de erro de validação, e 1 milhão cobre qualquer campanha realista.
  - **Relógio (B-1, aprovado em 2026-10-07):** toda regra de tempo (expiração, "hoje ou depois", fim do dia, `deactivated_at`) usa o relógio da função, por uma porta `Clock` injetada no domínio, o que permite testar com relógio fixo. Colunas só de registro (`created_at`, `clicked_at`) podem usar o `now()` do banco como padrão. A diferença entre os relógios da Vercel e do Neon (ambos com NTP) é de milissegundos e não muda nenhuma regra. Os `now()` dos rascunhos de SQL viram o parâmetro do `Clock` **[→ spec]**.
  - **Expiração:** o usuário escolhe uma **duração pronta** (1 h, 24 h, 7 dias ou 30 dias, e o servidor calcula `agora + duração`) **ou "até o fim do dia X"**, com um seletor só de data. Esse dia é interpretado em `America/Sao_Paulo`, o mesmo conceito de "dia" do dashboard: "fim do dia 30/10" vira `2026-10-30T23:59:59.999-03:00`.
    - **[→ spec]** A conversão não usa biblioteca: o offset vem do `Intl.DateTimeFormat` com `timeZone: 'America/Sao_Paulo'` e `timeZoneName: 'longOffset'`, que respeita a base IANA (devolve `GMT-02:00` para dezembro de 2018, ainda com horário de verão). O Node 24 não tem a API `Temporal`.
    - Mínimo: a data tem que ser hoje ou depois, no horário de Brasília. Máximo: **5 anos**, só como trava de sanidade (o máximo de um `Date` em JS é o ano 275760). Um limite de produto não faria sentido, porque o link sem expiração é permitido.
    - Descartados: data e hora livres com `datetime-local`, porque o valor chega sem fuso (`"2026-10-30T23:59"`) e o criador e o servidor podem estar em fusos diferentes; e só durações prontas, que não cobrem "campanha até o dia 30".
    - **Momento da expiração visível na tela (P7, decidido em 2026-09-30).** Escolher "até o fim de hoje" às 23h50 cria um link que dura 10 minutos: o comportamento é correto, mas surpreende. Por isso, embaixo do seletor de data, a tela mostra quando o link expira: "Expira em 30/10/2026 às 23:59 (horário de Brasília)" ou, se a data escolhida for hoje, "Expira **hoje** às 23:59 (horário de Brasília)".
      - O texto é só exibição, calculado no navegador com `Intl.DateTimeFormat` (`timeZone: 'America/Sao_Paulo'`), sem biblioteca. A regra do servidor não muda (hoje ou depois, até 5 anos), e um relógio errado no navegador só erra o rótulo.
      - O texto também deixa o fuso explícito para quem cria o link fora do horário de Brasília.
      - As durações prontas ("1 hora", "24 horas") se explicam sozinhas e não ganham texto.
      - Base: NN/g, "10 Usability Heuristics for User Interface Design", nº 1 (visibilidade do estado do sistema) e nº 5 (prevenção de erros).
      - Descartados: só documentar (a pessoa só descobre quando o link já expirou); proibir "hoje" (elimina o uso legítimo "evento hoje à noite"); e recusar quando faltar menos de 1 h (regra nova com limite arbitrário, e o aviso só chega depois do erro).
