// Filtro da lista de análises (seção e tema). Sem JS, a lista aparece completa e o filtro fica oculto.
(function () {
  var caixa = document.querySelector('[data-filtro]');
  var lista = document.querySelector('[data-lista]');
  if (!caixa || !lista) return;
  var itens = [].slice.call(lista.querySelectorAll('[data-secao]'));
  var vazio = lista.querySelector('[data-sem-resultado]');
  var contagem = caixa.querySelector('[data-contagem]');
  var estado = { secao: '', tema: '' };
  function aplica() {
    var n = 0;
    itens.forEach(function (el) {
      var ok = (!estado.secao || el.dataset.secao === estado.secao) && (!estado.tema || el.dataset.tema === estado.tema);
      el.hidden = !ok;
      if (ok) n++;
    });
    vazio.hidden = n !== 0;
    var sing = contagem.dataset.singular || 'análise';
    var plur = contagem.dataset.plural || 'análises';
    contagem.textContent = n + ' ' + (n === 1 ? sing : plur);
  }
  caixa.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-chave]');
    if (!b) return;
    estado[b.dataset.chave] = b.dataset.valor;
    caixa.querySelectorAll('button[data-chave="' + b.dataset.chave + '"]').forEach(function (x) {
      x.setAttribute('aria-pressed', String(x === b));
    });
    aplica();
  });
  caixa.hidden = false;
  aplica();
})();
