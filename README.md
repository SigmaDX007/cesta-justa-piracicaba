# Cesta Justa | Piracicaba e região

Aplicação **local, independente e sem serviços pagos** para encontrar varejões, feiras e indícios de produtores rurais próximos de Piracicaba, registrar cotações e comparar preços com evidência e unidade normalizada.

## Execução (Windows / Git Bash)

Na raiz do repositório:

```bash
bash ./run.sh
```

Requer Python 3.10+. O terminal mostra `http://127.0.0.1:8765` e tenta abrir o navegador. Não exige Node, NCM, chave de API, `pip` ou Docker. Para conferir o comportamento offline:

```bash
python -m unittest discover -s tests -v
```

O banco fica em `~/.cesta_justa_piracicaba/cesta.sqlite`, fora do Git. `Ctrl+C` encerra o servidor. É possível trocar a porta com `bash ./run.sh --port 8766`.

## Funcionalidades

- 28 **pontos de compra** (mercadão, varejões e feiras) extraídos da página oficial de Piracicaba, incluindo horários publicados; 8 produtores citados na Prefeitura e 1 rede de produtores. **Total inicial: 37 locais, nenhum preço fictício.**
- Descoberta opt-in e com cache de 24 horas de `shop=farm` e `shop=farm_shop` via OpenStreetMap Overpass, num raio de 40 km a partir do centro aproximado de Piracicaba. Esses dados são **pistas** e não certificação de venda direta. Não acessa contatos pessoais.
- Registro manual e importação CSV de preços, fonte, data, embalagem, variação, frete e tipo de evidência; deduplicação, histórico SQLite e exportação CSV.
- Conversão determinística `g↔kg`, `ml↔l`, `dúzia→unidade`. Pesquisa e ordenação por preço por unidade, com dados dos últimos sete dias como padrão.
- Atacado (CEAGESP/IEA/Prohort) marcado separadamente, excluído da comparação padrão. Valores de atacado **não são automaticamente acessíveis ao consumidor**.
- Sem coleta automática em plataformas protegidas, sem LLM, sem taxas de API e sem pagamento automático. Só escuta em `127.0.0.1`.

## Fluxo de uso

1. Abrir **Locais e produtores** e procurar por bairro. Abrir a fonte ou o mapa para confirmar horário, endereço e venda direta.
2. Em **Registrar informações**, selecionar o local e registrar preço da etiqueta/cotação ou importar CSV. Conservar variedade, peso, data e link da oferta quando existir.
3. Abrir **Comparar preços** e informar um produto. Comparar apenas produtos de qualidade/variedade equivalentes. Frete e pedido mínimo ainda exigem confirmação.

### CSV

CSV UTF-8 com separador ponto e vírgula e cabeçalho mínimo: `place_uid;produto;preco;quantidade;unidade;data`.

Exemplo **estrutural, não é preço real**:

```csv
place_uid;produto;preco;quantidade;unidade;data;tipo_evidencia
pref:piracicamirim;PRODUTO_EXEMPLO;10.00;1;kg;2026-11-22;observacao_usuario
```

Campos opcionais: `variacao;fonte_url;tipo_evidencia;frete;observacao`. Tipos: `observacao_usuario`, `cotacao_produtor`, `anuncio_publico`, `referencia_atacado`. Anúncios e referências atacadistas exigem URL pública.

## Fontes consultadas e proveniência

- Prefeitura de Piracicaba, [varejões e feiras livres](https://piracicaba.sp.gov.br/servicos/varejoes-municipais-e-feiras-livres/), atualização indicada: **05/05/2025**. Horários e endereços são históricos e devem ser confirmados antes do deslocamento. A página informa 24 varejões e 5 feiras, mas a tabela enumerada pode diferir; o programa usa somente os registros explicitamente apresentados.
- Prefeitura de Piracicaba, [Piracema de Sabores](https://piracicaba.sp.gov.br/noticias/piracema-de-sabores-destaca-produtores-locais-e-projetos-estudantis-no-varejao-da-paulista/): nomes de oito produtores locais, **sem preço, endereço ou contato individual confirmado**.
- [Rede Guandu](https://transforma.fbb.org.br/tecnologia-social/rede-guandu-producao-e-consumo-responsavel): referência de rede de agricultura familiar e compras coletivas. Verificar operação atual.
- [Selapir](https://piracicaba.sp.gov.br/servicos/selapir-selo-local-de-alimentos-de-piracicaba/): selo local para qualificação de fornecedores; nenhuma certificação de fornecedor individual é inferida.
- [CEAGESP](https://ceagesp.gov.br/cotacoes), [IEA](https://infoiea.agricultura.sp.gov.br/BancoDeDados/PrecosDiarios/Atacado): referências **atacadistas** para conferência, não preços finais de compra.
- [OpenStreetMap](https://www.openstreetmap.org/copyright): © contribuidores OSM (ODbL). Fonte consultada apenas mediante botão, 24h de cache, sem rastreamento em massa.

## Limitações e próximos incrementos

Sem tabela de preços atualizada publicamente e com granularidade por banca, **não há como prometer a opção mais barata sem obter cotações reais**. O app começa com zero cotações, e essa é a resposta correta. O módulo de rede pode ficar indisponível por limite público do Overpass, sem comprometer o modo offline. Pontos fora de Piracicaba dependem da busca OSM ou cadastro manual. Contatos, disponibilidade, qualidade, preços, pedido mínimo e frete devem ser validados com cada vendedor.

Melhorias possíveis: conector autorizado para tabela de preços de varejões da Sema; cesta multi-item com custo de deslocamento; horários por dia e geocodificação auditável; feeds de produtores com licença/API e testes de integração. **NCM não é necessário para comparação de preços ao consumidor**; só faria sentido em módulo fiscal futuro.

## Segurança / custos

API HTTP somente localhost, sem login remoto, limite de upload 1 MB, CSV e URLs validados, dados armazenados fora do repo, interface com escape HTML. Nenhuma chamada externa automática. Quando solicitado pelo usuário, a única consulta externa é ao Overpass e é limitada/cached. Não enviar mensagens para produtores nem executar compras sem confirmação explícita.


## Repositório independente e relação com SigmaDX

Este projeto foi estruturado para ser mantido em seu **próprio repositório Git** (`SigmaDX007/cesta-justa-piracicaba`), não como subpasta do projeto comercial. `sigmadx-analise-produtos` foi usado **somente como referência de engenharia**: documentação para agentes (`AGENTS.md`), testes determinísticos, processamento incremental, proveniência auditável, limites de custo e prevenção de duplicatas. Não há imports, credenciais, banco de dados, scripts de execução nem dependências do SigmaDX.

Referência de arquitetura: https://github.com/SigmaDX007/sigmadx-analise-produtos/tree/fix/gmail-collector

Leia também: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/STATUS.md`](docs/STATUS.md), [`docs/BACKLOG.md`](docs/BACKLOG.md).

### Publicação inicial no GitHub

Após criar o repositório vazio `SigmaDX007/cesta-justa-piracicaba` (sem README, `.gitignore` ou licença automática), execute na raiz desta cópia local, já inicializada com Git:

```bash
bash ./publish.sh
```

Requer autenticação GitHub no Git. Em máquinas com `git` já configurado, esse comando publica o histórico local. Não use token de acesso dentro de arquivos.

### Uso após publicação

```bash
git clone https://github.com/SigmaDX007/cesta-justa-piracicaba.git && cd cesta-justa-piracicaba && bash ./run.sh
```