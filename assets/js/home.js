// Home: cena WebGL ligada ao scroll, terminal que digita uma vez, entradas ao rolar e fachadas de vídeo e áudio.
// Sem laço contínuo: a cena só desenha um quadro quando a rolagem ou o tamanho da janela muda.
// Com movimento reduzido, nada se move: a cena desenha o símbolo parado e o terminal já aparece pronto.
import { Scene, PerspectiveCamera, WebGLRenderer, BufferGeometry, BufferAttribute, Points, PointsMaterial, Color, CanvasTexture, Group } from './vendor/three/three.module.js';

const raiz = document.documentElement;
raiz.classList.add('js');
const reduzido = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (reduzido) raiz.classList.add('reduzido');

/* ---------- Entradas ao rolar (uma vez) ---------- */
const alvos = document.querySelectorAll('.surgir, .capas, .podcast-grade');
if (reduzido || !('IntersectionObserver' in window)) {
  alvos.forEach((a) => a.classList.add('visivel'));
} else {
  const io = new IntersectionObserver((es) => {
    for (const e of es) if (e.isIntersecting) { e.target.classList.add('visivel'); io.unobserve(e.target); }
  }, { threshold: 0.15 });
  alvos.forEach((a) => io.observe(a));
}

/* ---------- Terminal: digita uma vez quando entra na tela ---------- */
const tela = document.querySelector('[data-terminal]');
if (tela && !reduzido && 'IntersectionObserver' in window) {
  const linhas = [...tela.querySelectorAll('.t-linha')];
  let terminou = false;
  let timer = 0;
  const terminar = () => {
    if (terminou) return;
    terminou = true;
    clearTimeout(timer);
    linhas.forEach((l) => { l.hidden = false; const c = l.querySelector('.t-cmd'); if (c && c.dataset.txt) c.textContent = c.dataset.txt; });
  };
  const comecar = () => {
    tela.style.minHeight = tela.offsetHeight + 'px'; // o terminal não muda de altura enquanto digita
    linhas.forEach((l) => {
      l.hidden = true;
      const c = l.querySelector('.t-cmd');
      if (c) { c.dataset.txt = c.textContent; c.textContent = ''; }
    });
    let i = 0;
    const proxima = () => {
      if (terminou) return;
      if (i >= linhas.length) { terminou = true; return; }
      const l = linhas[i++];
      l.hidden = false;
      const c = l.querySelector('.t-cmd');
      if (!c) { timer = setTimeout(proxima, 140); return; }
      const txt = c.dataset.txt;
      let k = 0;
      const tecla = () => {
        if (terminou) return;
        c.textContent = txt.slice(0, ++k);
        timer = k < txt.length ? setTimeout(tecla, 28 + Math.random() * 40) : setTimeout(proxima, 380);
      };
      timer = setTimeout(tecla, 320);
    };
    proxima();
  };
  let comecou = false;
  new IntersectionObserver(([e]) => {
    if (e.isIntersecting && !comecou) { comecou = true; comecar(); }
    else if (!e.isIntersecting && comecou) terminar(); // rolou para longe: termina na hora
  }, { threshold: 0.35 }).observe(tela);
}

/* ---------- Fachadas: o iframe de terceiros só carrega depois do clique ---------- */
document.querySelectorAll('.video').forEach((v) => {
  const id = v.dataset.id;
  if (!/^[\w-]{11}$/.test(id)) return;
  v.querySelector('a').addEventListener('click', (e) => {
    e.preventDefault();
    const f = document.createElement('iframe');
    f.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
    f.title = 'Vídeo';
    f.allow = 'autoplay; encrypted-media; picture-in-picture';
    f.referrerPolicy = 'strict-origin-when-cross-origin';
    f.allowFullscreen = true;
    v.replaceChildren(f);
    f.focus();
  });
});
document.querySelectorAll('.spotify').forEach((s) => {
  const id = s.dataset.show;
  if (!/^\w{22}$/.test(id)) return;
  s.querySelector('a').addEventListener('click', (e) => {
    e.preventDefault();
    const f = document.createElement('iframe');
    f.src = `https://open.spotify.com/embed/show/${id}`;
    f.title = 'Podcast no Spotify';
    f.allow = 'encrypted-media';
    f.loading = 'lazy';
    s.replaceChildren(f);
    f.focus();
  });
});

/* ---------- Cena WebGL ---------- */
const canvas = document.getElementById('cena');
if (canvas) iniciarCena(canvas);

function iniciarCena(canvas) {
  let renderer;
  try {
    renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'low-power' });
  } catch {
    canvas.remove(); // sem WebGL: fica o símbolo em SVG
    return;
  }
  const N = 2200;
  const formas = { simbolo: formaSimbolo(N), grade: formaGrade(N), onda: formaOnda(N), quadro: formaQuadro(N), som: formaSom(N) };
  const pecaB = formas.simbolo.pecaB; // 1 = peça B do símbolo (abre para cima e à direita)

  const cena = new Scene();
  const camera = new PerspectiveCamera(40, 1, 0.1, 50);
  camera.position.set(0, 0, 7.5);
  const grupo = new Group();
  cena.add(grupo);

  const pos = new Float32Array(N * 3);
  const geo = new BufferGeometry();
  geo.setAttribute('position', new BufferAttribute(pos, 3));
  const cores = new Float32Array(N * 3);
  geo.setAttribute('color', new BufferAttribute(cores, 3));
  const mat = new PointsMaterial({ size: 0.045, vertexColors: true, transparent: true, depthWrite: false, alphaMap: ponto(), alphaTest: 0.01 });
  grupo.add(new Points(geo, mat));

  const pintar = () => {
    const css = getComputedStyle(raiz);
    const a = new Color(css.getPropertyValue('--acento').trim() || '#FB5133');
    const b = new Color(css.getPropertyValue('--texto-3').trim() || '#9AA0A3');
    for (let i = 0; i < N; i++) {
      const c = (i % 5 === 0) ? b : a;
      cores[i * 3] = c.r; cores[i * 3 + 1] = c.g; cores[i * 3 + 2] = c.b;
    }
    geo.attributes.color.needsUpdate = true;
  };
  pintar();

  const secoes = [...document.querySelectorAll('[data-forma]')];
  const largo = () => innerWidth >= 900;

  const quadro = () => {
    pedido = 0;
    const w = innerWidth, h = innerHeight;
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, largo() ? 2 : 1.5));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();

    // t: posição contínua entre as seções (0 = hero, 1 = O que faço, ...), pelo centro da tela
    const meio = reduzido ? 0 : innerHeight / 2;
    let t = 0;
    if (!reduzido) {
      const centros = secoes.map((s) => { const r = s.getBoundingClientRect(); return r.top + r.height / 2; });
      if (meio <= centros[0]) t = 0;
      else if (meio >= centros[centros.length - 1]) t = centros.length - 1;
      else for (let i = 0; i < centros.length - 1; i++) {
        if (meio >= centros[i] && meio < centros[i + 1]) { t = i + (meio - centros[i]) / (centros[i + 1] - centros[i]); break; }
      }
    }
    const i0 = Math.floor(t), i1 = Math.min(i0 + 1, secoes.length - 1);
    const u = suave(t - i0);
    const A = formas[secoes[i0].dataset.forma], B = formas[secoes[i1].dataset.forma];
    // Abertura do símbolo ao rolar a hero: as peças se afastam ao longo da fenda (2.5, em sentido inverso)
    const heroAlt = secoes[0].offsetHeight || 1;
    const abre = reduzido ? 0 : Math.min(1, Math.max(0, scrollY / heroAlt)) * 0.55;
    for (let i = 0; i < N; i++) {
      let ax = A.p[i * 3], ay = A.p[i * 3 + 1], az = A.p[i * 3 + 2];
      if (A === formas.simbolo) { const s = pecaB[i] ? abre : -abre; ax += s; ay += s; }
      let bx = B.p[i * 3], by = B.p[i * 3 + 1], bz = B.p[i * 3 + 2];
      if (B === formas.simbolo) { const s = pecaB[i] ? abre : -abre; bx += s; by += s; }
      pos[i * 3] = ax + (bx - ax) * u;
      pos[i * 3 + 1] = ay + (by - ay) * u;
      pos[i * 3 + 2] = az + (bz - az) * u;
    }
    geo.attributes.position.needsUpdate = true;

    // Na hero o símbolo ocupa o lugar do SVG substituto (direita no desktop, abaixo do texto no celular);
    // nas outras seções vai para o fundo, à direita, maior e mais claro
    const naHero = Math.max(0, 1 - t);
    const lugar = ondeNaTela(document.querySelector('.hero-simbolo'), camera);
    const fundoX = largo() ? 1.6 : 0;
    grupo.position.x = lugar.x * naHero + fundoX * (1 - naHero);
    grupo.position.y = lugar.y * naHero;
    // giro leve e limitado: a forma nunca fica de perfil
    grupo.rotation.y = reduzido ? 0 : Math.sin(t * 1.6) * 0.28;
    grupo.rotation.x = reduzido ? 0 : Math.sin(t * 1.1) * 0.1;
    // fora da hero a forma fica maior e bem mais clara, atrás do conteúdo, para não competir com o texto
    grupo.scale.setScalar(lugar.escala * naHero + (largo() ? 1.45 : 1.1) * (1 - naHero));
    mat.opacity = 0.95 * naHero + 0.14 * (1 - naHero);
    renderer.render(cena, camera);
  };

  let pedido = 0;
  const agendar = () => { if (!pedido) pedido = requestAnimationFrame(quadro); };
  if (!reduzido) addEventListener('scroll', agendar, { passive: true });
  addEventListener('resize', agendar, { passive: true });
  matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => { pintar(); agendar(); });
  canvas.addEventListener('webglcontextlost', (e) => { e.preventDefault(); raiz.classList.remove('webgl'); });
  canvas.addEventListener('webglcontextrestored', () => { raiz.classList.add('webgl'); agendar(); });

  quadro();
  raiz.classList.add('webgl');
}

// Converte o centro e a largura de um elemento da página em posição e escala no plano z = 0 da cena.
function ondeNaTela(el, camera) {
  if (!el) return { x: 0, y: 0, escala: 1 };
  const r = el.getBoundingClientRect();
  const alturaMundo = 2 * Math.tan((camera.fov * Math.PI) / 360) * camera.position.z;
  const porPx = alturaMundo / innerHeight;
  // posição atual na tela: o símbolo acompanha a hero enquanto ela rola
  const cx = r.left + r.width / 2 - innerWidth / 2;
  const cy = r.top + r.height / 2 - innerHeight / 2;
  const escala = Math.min(r.width, r.height || r.width) * porPx / 3.2; // o símbolo mede cerca de 3,2 unidades
  return { x: cx * porPx, y: -cy * porPx, escala: Math.max(0.4, escala) };
}

/* ---------- Formas (coordenadas do mundo) ---------- */
function suave(x) { return x * x * (3 - 2 * x); }
function aleat(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

// Símbolo da marca: as duas peças exatas do DESIGN.md 3.3, amostradas por dentro (grade de 960).
function formaSimbolo(n) {
  const A = [[370, 200], [200, 370], [200, 595], [595, 200]];
  const B = [[200, 760], [590, 760], [760, 590], [760, 200], [645, 200], [200, 645]];
  const dentro = (x, y, poli) => {
    let d = false;
    for (let i = 0, j = poli.length - 1; i < poli.length; j = i++) {
      const [xi, yi] = poli[i], [xj, yj] = poli[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) d = !d;
    }
    return d;
  };
  const r = aleat(7), p = new Float32Array(n * 3), pecaB = new Uint8Array(n);
  let k = 0;
  while (k < n) {
    const x = 200 + r() * 560, y = 200 + r() * 560;
    const a = dentro(x, y, A), b = !a && dentro(x, y, B);
    if (!a && !b) continue;
    p[k * 3] = ((x - 480) / 280) * 1.55;
    p[k * 3 + 1] = (-(y - 480) / 280) * 1.55;
    p[k * 3 + 2] = (r() - 0.5) * 0.25;
    pecaB[k] = b ? 1 : 0;
    k++;
  }
  return { p, pecaB };
}

// Relatórios: três folhas A4 em leque, em grade de pontos.
function formaGrade(n) {
  const r = aleat(11), p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const f = i % 3, w = 1.5, h = w * 1.414;
    const x = (r() - 0.5) * w, y = (r() - 0.5) * h;
    const ang = (f - 1) * 0.22, ox = (f - 1) * 0.95;
    const qx = Math.round(x * 14) / 14, qy = Math.round(y * 14) / 14;
    p[i * 3] = ox + qx * Math.cos(ang) - qy * Math.sin(ang);
    p[i * 3 + 1] = qx * Math.sin(ang) + qy * Math.cos(ang);
    p[i * 3 + 2] = (f - 1) * -0.35;
  }
  return { p };
}

// Newsletter: uma superfície em onda, como páginas que passam.
function formaOnda(n) {
  const r = aleat(23), p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const x = (r() - 0.5) * 6, z = (r() - 0.5) * 3;
    p[i * 3] = x;
    p[i * 3 + 1] = Math.sin(x * 1.3) * 0.45 + Math.cos(z * 2.1 + x * 0.6) * 0.25 - 0.3;
    p[i * 3 + 2] = z;
  }
  return { p };
}

// Vídeos: contorno de um quadro 16:9 com o triângulo de reproduzir.
function formaQuadro(n) {
  const r = aleat(31), p = new Float32Array(n * 3);
  const w = 3.6, h = w * 9 / 16;
  for (let i = 0; i < n; i++) {
    let x, y;
    if (i % 4 === 3) {
      // triângulo de reproduzir
      const t = r(), s = r();
      const a = [-0.32, 0.38], b = [-0.32, -0.38], c = [0.42, 0];
      const lado = Math.floor(s * 3), q = [[a, b], [b, c], [c, a]][lado];
      x = q[0][0] + (q[1][0] - q[0][0]) * t; y = q[0][1] + (q[1][1] - q[0][1]) * t;
    } else {
      const per = 2 * (w + h), d = r() * per;
      if (d < w) { x = -w / 2 + d; y = h / 2; }
      else if (d < w + h) { x = w / 2; y = h / 2 - (d - w); }
      else if (d < 2 * w + h) { x = w / 2 - (d - w - h); y = -h / 2; }
      else { x = -w / 2; y = -h / 2 + (d - 2 * w - h); }
    }
    p[i * 3] = x; p[i * 3 + 1] = y; p[i * 3 + 2] = (r() - 0.5) * 0.08;
  }
  return { p };
}

// Podcast: forma de onda circular, como um sinal de áudio.
function formaSom(n) {
  const r = aleat(43), p = new Float32Array(n * 3), barras = 64;
  for (let i = 0; i < n; i++) {
    const bar = i % barras, ang = (bar / barras) * Math.PI * 2;
    const amp = 0.25 + 0.75 * Math.abs(Math.sin(bar * 1.7) * Math.cos(bar * 0.45));
    const rad = 1.1 + r() * amp;
    p[i * 3] = Math.cos(ang) * rad;
    p[i * 3 + 1] = Math.sin(ang) * rad;
    p[i * 3 + 2] = (r() - 0.5) * 0.1;
  }
  return { p };
}

// Textura redonda dos pontos.
function ponto() {
  const c = document.createElement('canvas');
  c.width = c.height = 32;
  const g = c.getContext('2d');
  g.fillStyle = '#fff';
  g.beginPath(); g.arc(16, 16, 14, 0, Math.PI * 2); g.fill();
  return new CanvasTexture(c);
}
