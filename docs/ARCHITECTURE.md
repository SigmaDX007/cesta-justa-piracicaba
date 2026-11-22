# Arquitetura

## Objetivo
Encontrar produtores/feiras/varejões de Piracicaba e região e comparar preços REAIS, com fonte/data/unidade, sem misturar dados de atacado e varejo.

## Componentes
- `server.py`: HTTP local (`127.0.0.1:8765`), API JSON e descoberta opcional via Overpass.
- `core.py`: SQLite, seed de locais, validação, normalização, importação CSV, preço por unidade, exportação.
- `static/index.html`: interface no navegador (sem JavaScript remoto).
- `data/places.csv`: 37 referências iniciais, com proveniência; não contém preços de ofertas.
- `tests/test_core.py`: testes offline determinísticos e proteção contra regressões.
- `.github/workflows/tests.yml`: testes automatizados no GitHub Actions.

## Fluxo de dados
1. Descoberta inicial (`data/places.csv`) ou consulta opt-in OpenStreetMap (cache 24h) -> locais potenciais.
2. Cadastro manual/importação CSV de oferta real -> validação (fonte, data, preço, unidade) -> SQLite local em diretório do usuário.
3. Consulta -> filtro de validade padrão 7 dias -> normalização de g/kg, ml/l, dúzia/un -> comparação por unidade.
4. Exportação CSV auditável para conferência offline.

## Fronteiras
- Nenhuma credencial, dado comercial, módulo Python ou banco do `sigmadx-analise-produtos` é utilizado.
- Nenhuma integração externa de preços é habilitada automaticamente.
- Referência de atacado não indica disponibilidade ao consumidor; excluir do ranking varejista padrão.
- Coleta automática paga e e-mails a fornecedores são tarefas futuras separadas, sujeitas a autorização.
