"""Limpeza do HTML replicado: lista de tags permitidas, sem script, iframe, formulário,
botão de assinatura nem pixel de rastreio. O resultado entra em arquivos Markdown que o Hugo
renderiza com `unsafe = true`, então tudo o que sai daqui precisa ser seguro por construção."""
import html
import re
from html.parser import HTMLParser

PERMITE = {"p", "h2", "h3", "h4", "ul", "ol", "li", "blockquote", "a", "strong", "b", "em", "i", "br", "hr",
           "img", "figure", "figcaption", "pre", "code", "table", "thead", "tbody", "tr", "th", "td", "sup", "sub", "u", "s"}
DESCARTA = {"script", "style", "iframe", "form", "button", "svg", "noscript", "object", "embed", "input", "select",
            "textarea", "template", "math", "head", "title", "frame", "frameset", "applet", "audio", "video", "canvas"}
CLASSES_DESCARTA = ("subscription-widget", "button", "subscribe", "share-", "post-ufi", "captioned-button",
                    "footnote-hovercard", "image-link-expand", "pencraft", "paywall",
                    "app-marketing", "app-banner", "substack-app", "mobile-app", "cta-wrapper")
VAZIAS = {"br", "hr", "img", "input", "meta", "link", "source", "area", "col", "base", "wbr", "embed", "track", "param"}
URL_IMG = re.compile(r"^https://[^\s\x00-\x1f]+$", re.I)
URL_LINK = re.compile(r"^(https?://|mailto:|#|/(?!/))[^\s\x00-\x1f]*$", re.I)


def _esc_attr(v):
    return html.escape(v, quote=True)


class Limpa(HTMLParser):
    """Estado de cada tag aberta na pilha: False = permitida (emitimos o fechamento),
    None = desconhecida (some a tag, fica o conteúdo), True = descartada com todo o conteúdo."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.pilha, self.pula = [], [], 0

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        cls = a.get("class", "").lower()
        if self.pula:
            if tag not in VAZIAS:
                self.pilha.append((tag, True))
                self.pula += 1
            return
        if tag in DESCARTA or (tag in ("div", "span", "a", "p") and any(c in cls for c in CLASSES_DESCARTA)):
            if tag not in VAZIAS:
                self.pilha.append((tag, True))
                self.pula = 1
            return
        if tag == "img":
            src = a.get("src", "").strip()
            if not URL_IMG.match(src):
                return
            if a.get("width") in ("0", "1") or a.get("height") in ("0", "1"):
                return
            self.out.append(f'<img src="{_esc_attr(src)}" alt="{_esc_attr(a.get("alt", ""))}" loading="lazy" referrerpolicy="no-referrer">')
            return
        if tag in PERMITE:
            at = ""
            if tag == "a":
                href = a.get("href", "").strip()
                if "substack.com/app/app-store-redirect" in href.lower():
                    self.pilha.append((tag, True))
                    self.pula = 1
                    return
                if URL_LINK.match(href):
                    at = f' href="{_esc_attr(href)}"'
                    if href.lower().startswith("http"):
                        at += ' rel="noopener noreferrer"'
            self.out.append(f"<{tag}{at}>")
            if tag not in VAZIAS:
                self.pilha.append((tag, False))
        elif tag not in VAZIAS:
            self.pilha.append((tag, None))

    def handle_endtag(self, tag):
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i][0] != tag:
                continue
            fechadas = self.pilha[i:]
            del self.pilha[i:]
            # fecha, de dentro para fora, tudo o que ficou aberto dentro desta tag
            for t, estado in reversed(fechadas):
                if estado is True:
                    self.pula -= 1
                elif estado is False and not self.pula:
                    self.out.append(f"</{t}>")
            self.pula = max(0, self.pula)
            return

    def handle_data(self, d):
        if not self.pula:
            self.out.append(html.escape(d, quote=False))

    def fecha_tudo(self):
        for t, estado in reversed(self.pilha):
            if estado is False and not self.pula:
                self.out.append(f"</{t}>")
            elif estado is True:
                self.pula -= 1
        self.pilha.clear()


def limpa_html(txt):
    p = Limpa()
    p.feed(txt or "")
    p.close()
    p.fecha_tudo()
    res = "".join(p.out)
    res = re.sub(r"<a\b[^>]*>\s*</a>", "", res)
    res = re.sub(r"<p>\s*(<br>)?\s*</p>", "", res)
    # o Hugo executa shortcodes ({{< >}} e {{% %}}) dentro do Markdown: nada vindo de fora pode abri-los
    res = res.replace("{{", "&#123;&#123;")
    return res.strip()


def resumo(txt, n=200):
    t = re.sub(r"<[^>]+>", " ", txt or "")
    t = re.sub(r"\s+", " ", html.unescape(t)).strip()
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",;:.") + "…"
