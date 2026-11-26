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

// Artigos em capas: a capa clicada sobe para a frente e os detalhes dela aparecem abaixo do leque.
(function () {
  var leque = document.querySelector('[data-leque]');
  if (!leque) return;
  leque.classList.add('leque-ativo');
  var ajuda = document.querySelector('[data-so-js]');
  if (ajuda) ajuda.hidden = false;
  var capas = leque.querySelectorAll('.leque-capa');
  var mostrar = function (alvo) {
    capas.forEach(function (c) {
      var sim = c === alvo;
      c.setAttribute('aria-expanded', String(sim));
      c.classList.toggle('ativa', sim);
      document.getElementById(c.getAttribute('aria-controls')).hidden = !sim;
    });
  };
  capas.forEach(function (c) { c.addEventListener('click', function () { mostrar(c); }); });
  mostrar(capas[0]); // o primeiro artigo já aparece aberto
})();

// Menu do celular: abre o painel, prende o foco dentro dele e fecha com Esc, com clique num link
// ou quando a tela passa de 640 px. No desktop o botão fica oculto pelo CSS e nada disso age.
(function () {
  var botao = document.querySelector('[data-menu-botao]');
  var menu = document.getElementById('menu-principal');
  if (!botao || !menu) return;
  var raiz = document.documentElement;
  var celular = window.matchMedia('(max-width: 639px)');
  var aberto = false;
  var focaveis = function () { return [botao].concat([].slice.call(menu.querySelectorAll('a'))); };
  function define(abrir, devolverFoco) {
    aberto = abrir;
    menu.classList.toggle('aberto', abrir);
    raiz.classList.toggle('menu-aberto', abrir);
    botao.setAttribute('aria-expanded', String(abrir));
    botao.setAttribute('aria-label', abrir ? botao.dataset.fechar : botao.dataset.abrir);
    if (abrir) { var l = menu.querySelector('a'); if (l) l.focus(); }
    else if (devolverFoco) botao.focus();
  }
  botao.addEventListener('click', function () { define(!aberto, true); });
  menu.addEventListener('click', function (e) { if (aberto && e.target.closest('a')) define(false, false); });
  document.addEventListener('keydown', function (e) {
    if (!aberto) return;
    if (e.key === 'Escape') { e.preventDefault(); define(false, true); return; }
    if (e.key !== 'Tab') return;
    var f = focaveis(), i = f.indexOf(document.activeElement);
    if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
  });
  var aoMudar = function () { if (!celular.matches && aberto) define(false, false); };
  if (celular.addEventListener) celular.addEventListener('change', aoMudar); else celular.addListener(aoMudar);
})();
