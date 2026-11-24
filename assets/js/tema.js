// Aplica o tema salvo antes da primeira pintura. Padrão: escuro (base da marca).
(function () {
  try {
    var t = localStorage.getItem('tema');
    if (t === 'claro' || t === 'escuro') document.documentElement.setAttribute('data-tema', t);
  } catch (e) { /* sem armazenamento: fica o escuro */ }
})();
