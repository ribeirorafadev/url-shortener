---
trigger: model_decision
description: "Google Safe Browsing (R7): privacidade, custo, cota, API key, indisponibilidade e mensagem de bloqueio. Ler ao mexer no adaptador do Safe Browsing ou na mensagem de URL suspeita."
---
# Segurança — blocklist (Google Safe Browsing)

## Blocklist: Google Safe Browsing (R7, incluída no MVP em 2026-09-30)
Regra de negócio em `.agents/context/url-validation.md` (R7). Aqui ficam os aspectos de segurança, privacidade e custo, verificados na documentação do Google em 2026-09-30:
- **Privacidade:** o adaptador usa o `hashes.search` da v5 e envia **só prefixos de 4 bytes do SHA-256**, nunca a URL. A comparação final é feita no nosso servidor. É a mesma política de minimização aplicada ao IP (LGPD, art. 6º, III).
- **Custo:** gratuito. "All use of Safe Browsing APIs is free of charge" (doc "Pricing") e "There is no cost for use of this API" (doc "Usage Restrictions"). Os termos são de **uso não comercial**; se o produto virar comercial, migrar para o Google Web Risk (mesma porta do domínio, só troca o adaptador).
- **Cota:** a documentação **não publica o número**. A cota padrão aparece no Google Cloud Console depois de ativar a API, e dá para pedir aumento sem custo. Fontes de terceiros citam 10 mil consultas por dia (não é número oficial). O consumo esperado é baixo: só a criação consulta, e ela já é limitada a 100 por dia por IP (10b).
- **Configuração (feita pelo Rafael):** conta Google → projeto no Google Cloud Console → criar a API key → ativar a "Safe Browsing API" (doc "Get started"). O passo a passo não pede conta de faturamento.
- **API key:**
  - só no servidor, via variável de ambiente `SAFE_BROWSING_API_KEY` (nunca no cliente nem em `NEXT_PUBLIC_*`);
  - **restrita no console à Safe Browsing API**, para uma chave vazada não servir para outras APIs do projeto;
  - vai na query string da chamada ao Google (`?key=`), então **nunca logar a URL da requisição** ao Google.
- **Serviço indisponível (B1): fail-closed**, com timeout de **2 s** na chamada. Com fail-open, um atacante com vários IPs poderia esgotar a cota diária de propósito e desligar a checagem quando quisesse. O redirect não depende do Google. Detalhes em `.agents/context/url-validation.md` (R7).
- **Adaptador:** fica em `src/infra/` (B2). A API key só é lida ali.
- **Mensagem de bloqueio (B3):** texto qualificado ("suspeito"), nunca afirmando certeza, mais a linha "Advisory provided by Google" com link para `https://developers.google.com/safe-browsing/v4/advisory`, e o aviso de falso positivo e falso negativo no README. São exigências da doc "Appropriate Usage" ("User warnings"). Texto final em `.agents/context/url-validation.md` (R7).
