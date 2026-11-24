# Site jeronimo.caxias.br

Site Hugo da marca **jeronimo molina**, no design system do repositório `design-system` (DESIGN.md v4.1.0): tema escuro por padrão, tema claro automático, Manrope, Inter e JetBrains Mono embutidas, acento `#FB5133` (`#C93414` no claro).

## O que o site mostra

| Página | De onde vem |
| --- | --- |
| Início | Últimas análises, vídeos e episódios |
| Newsletter | Substack (`jeronimomolina.substack.com`) |
| Podcast | Itens com áudio do Substack e, se houver, feeds de podcast |
| Vídeos | Feed do canal do YouTube |
| Nossa linha editorial, Sobre | Escritas à mão em `content/` |

Instagram, X, TikTok e LinkedIn não têm replicação automática (as plataformas não oferecem feed aberto); o rodapé só linka os perfis (`data/redes.yaml`).

## Como a replicação funciona

`ferramentas/sincronizar.py` lê os feeds públicos e cria arquivos em `content/newsletter`, `content/podcast` e `content/videos`, com `gerado: true` no front matter. O que não tem essa marca é seu e nunca é alterado. O script não apaga nada e, se uma fonte falhar, segue com as outras. O HTML passa por `ferramentas/limpeza.py`: lista de tags permitidas (sem script, iframe, formulário, botão de assinatura nem pixel de rastreio), só links `http(s)`, `mailto` e internos, e `{{` neutralizado para o Hugo não executar shortcode vindo de fora. O script só aceita feeds `https` e limita a resposta a 10 MB. As fontes ficam em `data/fontes.yaml`.

O workflow `.github/workflows/publicar.yml` roda a cada 3 horas e a cada push, em dois jobs: `replicar` (roda os testes, replica e grava o conteúdo novo; é o único com permissão de escrita) e `publicar` (gera o site e publica no GitHub Pages, sem escrita no repositório).

## Rodar localmente

```
pip install -r requirements.txt
python3 ferramentas/sincronizar.py        # lê a rede
python3 tests/testa_sincronizar.py        # teste offline (não escreve em content/)
hugo server --buildFuture
```

## Publicação

1. Settings > Pages > Source: GitHub Actions.
2. Custom domain: `jeronimo.caxias.br` (o arquivo `static/CNAME` já traz o nome). Para domínio próprio no Pages o repositório precisa ser público ou a conta ter plano que permita Pages em repositório privado.
3. No registro.br, no DNS de `jeronimo.caxias.br`: registros `A` para `185.199.108.153`, `185.199.109.153`, `185.199.110.153` e `185.199.111.153`, e `AAAA` para `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153` e `2606:50c0:8003::153`.
4. Marque "Enforce HTTPS" depois que o GitHub emitir o certificado.
5. Os demais domínios (derossi.dev, derossi.lt e outros) redirecionam para este endereço, no painel de cada registrador.

## Antes de ligar o canal do YouTube

O handle `@jeronimomolina` vem da memória de redes de 23/11/2026. Se o canal usar outro nome, corrija `data/fontes.yaml`; o script descobre o `channel_id` sozinho.

## Segurança

- Cada página manda uma Content-Security-Policy por `<meta>` (sem script ou estilo inline; imagens e áudio só por https; iframe só do `youtube-nocookie.com`). O GitHub Pages não deixa configurar cabeçalhos HTTP, então a política vai no HTML.
- `markup.goldmark.renderer.unsafe = true` é necessário para o HTML escrito à mão em `content/`. Por isso todo texto replicado passa pela limpeza antes de virar arquivo.
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
