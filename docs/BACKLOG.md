# Backlog

## P0 - MVP (implementado)
- [x] Aplicação web local sem dependências pagas.
- [x] Diretório inicial de varejões, feiras e pistas de produtores.
- [x] SQLite local, registro/importação de preços e exportação CSV.
- [x] Normalização de unidades, validade, idempotência e segregação do atacado.
- [x] Testes offline e workflow CI independente.

## P1 - Prospecção e preços (pendente)
- [ ] Encontrar feeds oficiais ou autorizados de ofertas com data e fonte.
- [ ] Verificar disponibilidade, contato comercial, distância e pedido mínimo por produtor.
- [ ] Criar lista de compras multi-itens e custo final incluindo frete/deslocamento.
- [ ] Automatizar coleta incremental com cache/limite de requisições e casos de erro.
- [ ] Criar painel de confiabilidade de cada observação (manual, URL pública, confirmação comercial).

## P2 - Qualidade e operação (pendente)
- [ ] Geocodificação auditável e comparação de raio de busca.
- [ ] Contratos de fontes externos com testes de integração gravados/mocks.
- [ ] Observabilidade de latência, falhas de fonte e frescor dos preços.
