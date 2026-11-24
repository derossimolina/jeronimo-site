# DESIGN.md — site jeronimo.caxias.br

Brief de design deste site. A fonte de verdade visual é o design system da marca (`derossimolina/design-system`, **DESIGN.md v4.1.0**): tokens, tipografia, componentes, voz e acessibilidade vêm de lá. Este arquivo registra só o que é próprio do site.

## Produto

- **O que é:** a casa da marca jeronimo molina. Reúne newsletter (Substack), vídeos (YouTube) e podcast (Spotify).
- **Para quem:** quem chega pela primeira vez e precisa entender em segundos quem assina e o que é publicado; quem volta para ver o que saiu de novo.
- **Próxima ação da home:** rolar até o conteúdo e abrir uma análise.

## Sistema

- Tokens em `assets/css/site.css` (`:root`), copiados do anexo 7.6 do design system. O tema segue `prefers-color-scheme`.
- O terminal da home usa os valores do tema escuro da paleta nos dois temas (`--term-*`).

## Decisões

| Data | Decisão | Por quê |
| --- | --- | --- |
| 24/11/2026 | Rodapé só com ícones das redes (Simple Icons, CC0) e do RSS (Lucide), com nome acessível e alvo de 44 px; saem Linha editorial e Sobre, que estão no cabeçalho | Pedido da pessoa responsável; o RSS ficaria sem link visível |
| 24/11/2026 | Home: hero sem botões; seções "O que faço", Newsletter, Vídeos e Podcast, nessa ordem de rolagem | Pedido da pessoa responsável |
| 24/11/2026 | Cena WebGL com Three.js 0.187 servido do próprio site (`assets/js/vendor/three`, licença MIT): pontos que formam o símbolo na hero e mudam de forma por seção (folhas, onda, quadro 16:9, sinal de áudio) | Escolha da pessoa responsável (Three.js local em vez de WebGL puro) |
| 24/11/2026 | **Exceção controlada à seção 2.5** do design system: a cena só desenha quando a rolagem muda (sem laço), o terminal digita uma vez e o cursor pisca 3 vezes; com movimento reduzido, nada se move e a cena fica só na hero; sem WebGL, fica o símbolo hachurado em SVG | O 2.5 pede movimento curto e sem decoração; a pessoa aprovou esta exceção em 24/11/2026 |
| 24/11/2026 | Modelo de capa de relatório (`layouts/partials/capa-relatorio.html`), proporção A4, preenchido com título e data reais das análises; também substitui a imagem de post sem imagem (versão 16:9) | Nada inventado nas capas |
| 24/11/2026 | Terminal no estilo Ghostty com prompt do oh-my-bash, só com textos reais (slugs e título da última análise) e o método publicado (fato, fonte, posição) | Ilustra o processo sem dado fabricado |
| 24/11/2026 | Podcast sem episódios no site: player do Spotify (show) carregado só após clique; CSP passa a aceitar `open.spotify.com` em `frame-src` | Não há feed RSS do podcast ainda |
| 24/11/2026 | Canal do YouTube corrigido para `@jderossimolina` | Informado pela pessoa responsável |

## Perguntas em aberto

- A exceção ao 2.5 (cena WebGL e terminal) entra no design system como regra para o site ou fica só aqui?
- RSS do podcast no host, para listar os episódios na home em vez do player do show.
- Peso do Three.js: o pacote da home tem cerca de 136 KB (gzip). Aceitável, ou trocar por WebGL puro depois?
