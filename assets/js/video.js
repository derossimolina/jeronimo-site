// Troca a capa do vídeo pelo player (youtube-nocookie) só quando a pessoa clica.
document.querySelectorAll('.video').forEach(function (v) {
  var id = v.dataset.id;
  if (!/^[\w-]{11}$/.test(id)) return;
  v.querySelector('a').addEventListener('click', function (e) {
    e.preventDefault();
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0';
    f.title = v.dataset.titulo || 'Vídeo';
    f.allow = 'autoplay; encrypted-media; picture-in-picture';
    f.referrerPolicy = 'strict-origin-when-cross-origin';
    f.allowFullscreen = true;
    v.replaceChildren(f);
    f.focus();
  });
});
