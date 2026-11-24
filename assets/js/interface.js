// Alternador de tema (todas as páginas) e revelação dos blocos de texto ao rolar (página Sobre).
(function () {
  var raiz = document.documentElement;
  raiz.classList.add('js');

  var botao = document.querySelector('[data-alternar-tema]');
  if (botao) {
    var atualizar = function () {
      var claro = raiz.getAttribute('data-tema') === 'claro';
      botao.setAttribute('aria-pressed', String(claro));
      botao.querySelector('[data-rotulo]').textContent = claro ? botao.dataset.escuro : botao.dataset.claro;
    };
    botao.addEventListener('click', function () {
      var novo = raiz.getAttribute('data-tema') === 'claro' ? 'escuro' : 'claro';
      raiz.setAttribute('data-tema', novo);
      try { localStorage.setItem('tema', novo); } catch (e) { /* vale só nesta página */ }
      atualizar();
    });
    atualizar();
  }

  // Texto que aparece aos poucos: cada bloco da prosa entra quando chega à tela, uma vez.
  var prosa = document.querySelector('.prosa[data-revelar]');
  if (!prosa) return;
  var blocos = prosa.children;
  var reduzido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduzido || !('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('visivel'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -12% 0px' });
  for (var i = 0; i < blocos.length; i++) {
    var r = blocos[i].getBoundingClientRect();
    if (r.top < window.innerHeight) continue; // o que já está na tela não some
    blocos[i].classList.add('a-revelar');
    io.observe(blocos[i]);
  }
})();

// Cards empilhados dos artigos: o card clicado sobe e mostra os detalhes; um aberto por vez.
(function () {
  var pilha = document.querySelector('[data-pilha]');
  if (!pilha) return;
  pilha.classList.add('pilha-ativa');
  var ajuda = document.querySelector('[data-so-js]');
  if (ajuda) ajuda.hidden = false;
  var botoes = pilha.querySelectorAll('.artigo-botao');
  var abrir = function (alvo) {
    botoes.forEach(function (b) {
      var aberto = b === alvo && b.getAttribute('aria-expanded') !== 'true';
      b.setAttribute('aria-expanded', String(aberto));
      b.closest('.pilha-item').classList.toggle('aberta', aberto);
      document.getElementById(b.getAttribute('aria-controls')).inert = !aberto;
    });
  };
  botoes.forEach(function (b) {
    b.setAttribute('aria-expanded', 'false');
    document.getElementById(b.getAttribute('aria-controls')).inert = true;
    b.addEventListener('click', function () { abrir(b); });
  });
})();
