# DESIGN.md — site jeronimo.caxias.br

Brief de design deste site. A fonte de verdade visual é o design system da marca (`derossimolina/design-system`, **DESIGN.md v4.1.0**): tokens, tipografia, componentes, voz e acessibilidade vêm de lá. Este arquivo registra só o que é próprio do site.

## Produto

- **O que é:** a casa da marca jeronimo molina. Reúne newsletter (Substack), vídeos (YouTube) e podcast (Spotify).
- **Para quem:** quem chega pela primeira vez e precisa entender em segundos quem assina e o que é publicado; quem volta para ver o que saiu de novo.
- **Próxima ação da home:** rolar até o conteúdo e abrir uma análise.

## Sistema

- Tokens em `assets/css/site.css` (`:root`), copiados do anexo 7.6 do design system. Tema escuro por padrão; o claro vem do botão do cabeçalho (`data-tema="claro"`), salvo no navegador.
- Idiomas: português na raiz e inglês em `/en/` (textos de interface em `i18n/`). O conteúdo replicado só existe em português e aparece nas listas em inglês com `lang="pt-BR"`.
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
| 24/11/2026 | "Sobre" e "Nossa linha editorial" viram uma página só, "Sobre" (`/sobre/`); `/nossa-linha-editorial/` redireciona para ela; sai do menu | Pedido da pessoa responsável |
| 24/11/2026 | Ordem da página Sobre: quem assina, análise, pesquisa e doutorado (com os artigos), método e linha; filiação partidária no fim, com o texto aprovado sem mudança | Mais ênfase em análise e doutorado; a filiação continua declarada (design system 5.2) |
| 24/11/2026 | Sai a linha de versão ("Versão 1, de 23/11/2026...") e a frase de vigência da página | Não faz sentido para quem lê |
| 24/11/2026 | Texto da página Sobre justificado (com hifenização), na mesma coluna, e cada bloco aparece ao chegar à tela (opacidade e 16 px, 400 ms, uma vez); sem JS ou com movimento reduzido, tudo visível | Pedido da pessoa responsável |
| 24/11/2026 | Artigos publicados em cards empilhados (`data/publicacoes.yaml`, shortcode `publicacoes`): o card clicado sobe e mostra autoria, periódico, DOI, citação ABNT e link; botão com `aria-expanded`; sem JS, lista aberta | Só os 3 artigos em periódico confirmados (Hoplos 2024, Gestão.org 2024, RBGI 2022); o Google Scholar bloqueou a consulta automática, os dados vêm do Crossref, do OpenAlex e das revistas |
| 24/11/2026 | Tema claro por botão no cabeçalho, escuro como padrão | Escolha da pessoa responsável |
| 24/11/2026 | Versão em inglês de interface, home e Sobre (tradução em rascunho); análises, vídeos e episódios continuam em português | Escolha da pessoa responsável |

## Perguntas em aberto

- A exceção ao 2.5 (cena WebGL e terminal) entra no design system como regra para o site ou fica só aqui?
- Revisar a tradução para o inglês (`content/*.en.md`, `i18n/en.yaml`) e os blocos novos da página Sobre ("Análise" e "Pesquisa e doutorado").
- Outras produções (Libertarianismo no Poder, 2019; Virtual Sensemaking, 2020; preprint no Zenodo, 2026) ficaram fora dos cards; entram se você quiser.
- RSS do podcast no host, para listar os episódios na home em vez do player do show.
- Peso do Three.js: o pacote da home tem cerca de 136 KB (gzip). Aceitável, ou trocar por WebGL puro depois?
