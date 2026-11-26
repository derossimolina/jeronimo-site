# Site jeronimo.caxias.br

Site Hugo da marca **jeronimo molina**, no design system do repositório `design-system` (DESIGN.md v4.1.0): tema escuro por padrão, tema claro automático, Manrope, Inter e JetBrains Mono embutidas, acento `#FB5133` (`#C93414` no claro).

## O que o site mostra

| Página | De onde vem |
| --- | --- |
| Início | Últimas análises, vídeos e episódios |
| Newsletter | Substack (`jeronimomolina.substack.com`) |
| Podcast | Itens com áudio do Substack e, se houver, feeds de podcast |
| Vídeos | Feed do canal do YouTube |
| Análises | Escritas no Obsidian (`D:/Notas/21 Conteúdo/Análises`) e trazidas por `ferramentas/importar_analises.py` |
| Sobre (inclui a linha editorial) | Escrita à mão em `content/` |

Instagram, X, TikTok e LinkedIn não têm replicação automática (as plataformas não oferecem feed aberto); o rodapé só linka os perfis (`data/redes.yaml`).

## Como a replicação funciona

`ferramentas/sincronizar.py` lê os feeds públicos e cria arquivos em `content/newsletter`, `content/podcast` e `content/videos`, com `gerado: true` no front matter. O que não tem essa marca é seu e nunca é alterado. O script não apaga nada e, se uma fonte falhar, segue com as outras. O HTML passa por `ferramentas/limpeza.py`: lista de tags permitidas (sem script, iframe, formulário, botão de assinatura nem pixel de rastreio), só links `http(s)`, `mailto` e internos, e `{{` neutralizado para o Hugo não executar shortcode vindo de fora. O script só aceita feeds `https` e limita a resposta a 10 MB. As fontes ficam em `data/fontes.yaml`.

O workflow `.github/workflows/publicar.yml` roda a cada 3 horas e a cada push, em três jobs: `replicar` (roda os testes, replica e grava o conteúdo novo; é o único com permissão de escrita no repositório), `gerar` (gera o site com Hugo e envia o artefato) e `publicar` (faz o deploy no GitHub Pages).

## Análises: do Obsidian para o site

1. No cofre, crie a nota em `21 Conteúdo/Análises` a partir do modelo `91 Modelos/Análise.md`. As propriedades e os títulos `## O que aconteceu`, `## Minha leitura`, `## Probabilidade e horizonte`, `## O que observar`, `## Quem é afetado` e `## Correções` viram a ficha, exibida acima do texto.
2. Quando estiver pronta, marque `publicar: true`.
3. No repositório do site: `py -3.12 ferramentas/importar_analises.py` mostra a prévia; `--gravar` grava em `content/analises/` (e as imagens em `static/analises/`).
4. Confira com `hugo server`, faça o commit e o push.

O script lê o cofre sem alterar nada e barra a nota com fato sem link ou sem data, probabilidade fora da escala (`data/escalas.yaml`), rótulo proibido, termo vetado pelo design system ou imagem sem texto alternativo. Comentários `%% %%`, callouts e nomes de notas não publicadas não vão para o site. Ele só regrava arquivos com `importado: true`; o `sincronizar.py` nunca toca em `content/analises/`. O CI não lê o cofre: a importação roda só no seu computador.

## Rodar localmente

```
pip install -r requirements.txt
python3 ferramentas/sincronizar.py        # lê a rede
python3 tests/testa_sincronizar.py        # teste offline (não escreve em content/)
python3 tests/testa_importar.py           # teste offline da importação do Obsidian
hugo server --buildFuture
```

## Publicação

1. Settings > Pages > Source: GitHub Actions.
2. Custom domain: `jeronimo.caxias.br` (o arquivo `static/CNAME` já traz o nome). Para domínio próprio no Pages o repositório precisa ser público ou a conta ter plano que permita Pages em repositório privado.
3. No registro.br, no DNS de `jeronimo.caxias.br`: registros `A` para `185.199.108.153`, `185.199.109.153`, `185.199.110.153` e `185.199.111.153`, e `AAAA` para `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153` e `2606:50c0:8003::153`.
4. Marque "Enforce HTTPS" depois que o GitHub emitir o certificado.
5. Os demais domínios (derossi.dev, derossi.lt e outros) redirecionam para este endereço, no painel de cada registrador.

## Antes de ligar o canal do YouTube

O handle `@jderossimolina` está configurado em `data/fontes.yaml`; o script descobre o `channel_id` sozinho.

## Segurança

- Cada página manda uma Content-Security-Policy por `<meta>` (sem script ou estilo inline; `connect-src 'none'`; `worker-src 'none'`; imagens e áudio só por `https:`; iframes só de `youtube-nocookie.com` e `open.spotify.com`). O GitHub Pages não deixa configurar cabeçalhos HTTP, então a política vai no HTML; para adicionar `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, HSTS e `Permissions-Policy`, recomenda-se colocar o domínio atrás do Cloudflare (proxy DNS + *Response Header Transform Rules*).
- `markup.goldmark.renderer.unsafe = true` é necessário para o HTML escrito à mão em `content/`. Por isso todo texto replicado passa por `ferramentas/limpeza.py` (somente tags permitidas, imagens exclusivamente `https://`, neutralização de `{{`) e `ferramentas/sincronizar.py` valida URLs `https://` inclusive em redirecionamentos e campos do front matter.
- Actions e dependências são atualizadas pelo Dependabot (`.github/dependabot.yml`).

## Estrutura

```
assets/        css e js (fingerprint + SRI)
content/       páginas à mão e conteúdo replicado (gerado: true)
data/          fontes.yaml, redes.yaml
ferramentas/   sincronizar.py (rede, escrita) e limpeza.py (HTML seguro)
layouts/       tema
static/        fontes, favicon, CNAME
tests/         testes offline e fixtures
```
