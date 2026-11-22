# Orientações para GPT/Codex — Cesta Justa

Objetivo: identificar pontos locais de venda direta e construir histórico de preços de alimentos com fonte, data, comparabilidade e controle de custo. Este app é isolado dos bancos, credenciais e pipelines comerciais do SigmaDX.

- Ler README e testes antes de qualquer edição. Usar Python 3.10+, stdlib, `unittest` e SQLite. Não instalar APIs pagas/LLMs/MCPs sem necessidade real e autorização.
- Nunca inventar cotação, contato, horário, certificação, produtor direto ou preço de compra. `referencia_atacado` é diferente de cotação varejista; manter essa segregação.
- Não combinar `kg`, `l` e `un`; normalizar variações explícitas, manter frete separado e evitar comparação entre variedades distintas quando possível.
- Importações devem ser idempotentes, ter data e, se houver, URL de origem. OSM é indício não validado, com cache e uso proporcional.
- Não coletar contatos pessoais nem vasculhar Gmail, WhatsApp, grupos ou sites protegidos. Servir somente em localhost.
- Rodar `python -m unittest discover -s tests -v` antes de afirmar que funciona. Documentar falhas e lacunas no README; não alterar snapshots de bancos do SigmaDX.

## Regras de arquitetura para extensões

- Este repositório é independente; referências ao SigmaDX são exclusivamente conceituais. Não alterar o repositório de fornecedores ao desenvolver Cesta Justa.
- Antes de modificar `core.py`, `server.py` ou a interface, consultar `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/BACKLOG.md` e os testes.
- Manter `docs/STATUS.md` baseado em execução observada; atualizar backlog e decisões ao adicionar conectores.
- Preferir integrações de preços com autorização, cache, orçamento zero por padrão e evidência vinculada a data e URL. Não apresentar preços de atacado como disponíveis ao consumidor.
- Teste principal: `python -m unittest discover -s tests -v`. Testar também `python -m py_compile core.py server.py`.