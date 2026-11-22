# Decisões técnicas

- **ADR-001: Repositório separado.** O projeto de alimentos deve ter versionamento, documentação, CI e banco próprios. SigmaDX é apenas referência de arquitetura, não dependência.
- **ADR-002: Python stdlib + SQLite.** Baixo custo e inicialização local sem pip, Docker ou Node. Futuras dependências precisam de benefício explícito.
- **ADR-003: Verdade sobre preços.** O sistema começa sem cotações reais e nunca gera valores fictícios. Só compara dados atribuídos a fonte, data, unidade e local.
- **ADR-004: Classificação de dados.** Preços de atacado ficam apartados de compras varejistas; locais OSM são indícios, não produtores verificados.
- **ADR-005: Limites externos.** OpenStreetMap opcional e com cache; nenhuma busca comercial paga ou acesso Gmail autorizado nesta aplicação.
