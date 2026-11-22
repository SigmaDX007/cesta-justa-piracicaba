# Status

Projeto independente publicado no repositório `SigmaDX007/cesta-justa-piracicaba`. Código sem dependências do SigmaDX.

- **Implementado:** servidor HTTP local, diretório de 37 locais, preços manuais/CSV, SQLite, consulta OSM opt-in, comparador por unidade, testes offline.
- **Não implementado:** conectores automáticos de cotações de produtores e ranking com frete real.
- **Não presumir:** que algum produtor vende diretamente ou que o app conhece o menor preço sem cotações atuais.
- **Evidência local:** `python -m unittest discover -s tests -v` executou 14 testes com OK em 22/11/2026 na cópia ZIP anterior à publicação. GitHub Actions requer verificação separada.
