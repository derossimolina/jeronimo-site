#!/usr/bin/env python3
"""Replica newsletter, podcast e vídeos para content/ a partir dos feeds públicos.

Fontes (data/fontes.yaml):
  substack         feed RSS https://HOST/feed; item com áudio vira podcast, o resto vira newsletter
  podcast_feeds    feeds RSS de podcast fora do Substack
  youtube          feed Atom do canal (por @handle ou channel_id)

Regras:
  - Só cria ou atualiza arquivos com `gerado: true` no front matter. Arquivo sem essa marca é
    seu: o script nunca toca nele.
  - Nunca apaga nada. Se uma fonte falhar, avisa e segue com as outras.
  - O HTML de cada texto passa por uma lista de tags permitidas (sem script, iframe, formulário,
    botão de assinatura nem pixel de rastreio).

Uso:
  python3 ferramentas/sincronizar.py                  # lê a rede
  python3 ferramentas/sincronizar.py --offline DIR    # lê DIR/{substack,podcast,youtube}-*.xml (testes)
"""
import argparse, html, re, sys, unicodedata, urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml

RAIZ = Path(__file__).resolve().parents[1]
NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "media": "http://search.yahoo.com/mrss/",
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}
UA = "Mozilla/5.0 (compatible; jeronimo-site-sync/1.0; +https://jeronimo.caxias.br)"


# ------------------------------------------------------------------ rede
def baixa(url, tentativas=3):
    ultimo = None
    for _ in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            ultimo = e
    raise RuntimeError(f"{url}: {ultimo}")


# ------------------------------------------------------------------ texto
def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80] or "sem-titulo"


def data_iso(txt):
    txt = (txt or "").strip()
    try:
        d = parsedate_to_datetime(txt)
    except Exception:  # noqa: BLE001
        try:
            d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


PERMITE = {"p", "h2", "h3", "h4", "ul", "ol", "li", "blockquote", "a", "strong", "b", "em", "i", "br", "hr",
           "img", "figure", "figcaption", "pre", "code", "table", "thead", "tbody", "tr", "th", "td", "sup", "sub", "u", "s"}
DESCARTA = {"script", "style", "iframe", "form", "button", "svg", "noscript", "object", "embed", "input", "select", "textarea"}
CLASSES_DESCARTA = ("subscription-widget", "button", "subscribe", "share-", "post-ufi", "captioned-button",
                    "footnote-hovercard", "image-link-expand", "pencraft", "paywall")
VAZIAS = {"br", "hr", "img", "input", "meta", "link", "source", "area", "col", "base", "wbr", "embed", "track", "param"}


class Limpa(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.pilha, self.pula = [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").lower()
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
            src = a.get("src") or ""
            if not src.startswith("http"):
                return
            w, h = a.get("width", ""), a.get("height", "")
            if w in ("0", "1") or h in ("0", "1"):
                return
            alt = html.escape(a.get("alt") or "", quote=True)
            self.out.append(f'<img src="{html.escape(src, quote=True)}" alt="{alt}" loading="lazy">')
            return
        if tag in PERMITE:
            at = ""
            if tag == "a":
                href = a.get("href") or ""
                if re.match(r"^(https?:|mailto:|#|/)", href):
                    at = f' href="{html.escape(href, quote=True)}"'
                    if href.startswith("http"):
                        at += ' rel="noopener"'
            self.out.append(f"<{tag}{at}>")
            if tag not in VAZIAS:
                self.pilha.append((tag, False))
        else:
            # tag desconhecida (div, span, section...): descarta a tag e mantém o conteúdo
            if tag not in VAZIAS:
                self.pilha.append((tag, None))

    def handle_endtag(self, tag):
        for i in range(len(self.pilha) - 1, -1, -1):
            if self.pilha[i][0] == tag:
                _, estado = self.pilha[i]
                del self.pilha[i:]
                if estado is True:
                    self.pula = max(0, self.pula - 1)
                elif estado is False and not self.pula:
                    self.out.append(f"</{tag}>")
                return

    def handle_data(self, d):
        if not self.pula:
            self.out.append(html.escape(d, quote=False))


def limpa_html(txt):
    p = Limpa()
    p.feed(txt or "")
    p.close()
    res = "".join(p.out)
    res = re.sub(r"<p>\s*(<br>)?\s*</p>", "", res)
    return res.strip()


def resumo(txt, n=200):
    t = re.sub(r"<[^>]+>", " ", txt or "")
    t = re.sub(r"\s+", " ", html.unescape(t)).strip()
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


# ------------------------------------------------------------------ escrita
def escreve(pasta, nome, fm, corpo, relatorio):
    pasta.mkdir(parents=True, exist_ok=True)
    f = pasta / nome
    if f.exists() and "gerado: true" not in f.read_text(encoding="utf-8").split("---", 2)[1]:
        relatorio["ignorados"] += 1
        return
    fm = {**fm, "gerado": True}
    novo = "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=1000) + "---\n\n" + corpo.strip() + "\n"
    if f.exists() and f.read_text(encoding="utf-8") == novo:
        relatorio["iguais"] += 1
        return
    f.write_text(novo, encoding="utf-8")
    relatorio["escritos"] += 1


def txt(el, caminho):
    x = el.find(caminho, NS)
    return (x.text or "").strip() if x is not None and x.text else ""


# ------------------------------------------------------------------ fontes
def itens_rss(xml):
    raiz = ET.fromstring(xml)
    canal = raiz.find("channel")
    for it in canal.findall("item"):
        enc = it.find("enclosure")
        img = it.find("itunes:image", NS)
        yield {
            "titulo": txt(it, "title"),
            "link": txt(it, "link"),
            "data": data_iso(txt(it, "pubDate")),
            "descricao": txt(it, "description"),
            "corpo": txt(it, "content:encoded"),
            "autor": txt(it, "dc:creator") or txt(it, "itunes:author"),
            "audio": enc.get("url") if enc is not None and (enc.get("type") or "").startswith("audio") else "",
            "audio_tipo": enc.get("type") if enc is not None else "",
            "duracao": txt(it, "itunes:duration"),
            "imagem": (enc.get("url") if enc is not None and (enc.get("type") or "").startswith("image") else "")
                      or (img.get("href") if img is not None else ""),
        }


def monta_post(i, marca, tipo):
    corpo = limpa_html(i["corpo"] or i["descricao"])
    desc = resumo(i["descricao"]) or resumo(corpo)
    slug = slugify(i["link"].rstrip("/").rsplit("/", 1)[-1] if "/p/" in i["link"] else i["titulo"])
    fm = {"title": i["titulo"], "date": i["data"].strftime("%Y-%m-%dT%H:%M:%S+00:00") if i["data"] else None,
          "slug": slug, "description": desc, "marca": marca, "origem": i["link"]}
    if i["imagem"]:
        fm["imagem"] = i["imagem"]
    if tipo == "podcast":
        fm["audio"] = i["audio"]
        if i["duracao"]:
            fm["duracao"] = i["duracao"]
    fm = {k: v for k, v in fm.items() if v not in (None, "")}
    nome = f"{i['data']:%Y-%m-%d}-{slug}.md" if i["data"] else f"{slug}.md"
    return nome, fm, corpo


def sync_substack(cfg, xml_por_host, rel):
    for fonte in cfg.get("substack", []):
        host = fonte["host"]
        try:
            xml = xml_por_host(host)
            n = 0
            for i in itens_rss(xml):
                if n >= cfg.get("max_itens", 60) or not i["titulo"]:
                    break
                tipo = "podcast" if i["audio"] else "newsletter"
                nome, fm, corpo = monta_post(i, fonte["marca"], tipo)
                escreve(RAIZ / "content" / tipo, nome, fm, corpo, rel)
                n += 1
            print(f"OK     substack {host}: {n} itens")
        except Exception as e:  # noqa: BLE001
            rel["falhas"].append(f"substack {host}: {e}")
            print(f"AVISO  substack {host}: {e}")


def sync_podcasts(cfg, baixa_url, rel):
    for fonte in cfg.get("podcast_feeds") or []:
        try:
            xml = baixa_url(fonte["url"])
            n = 0
            for i in itens_rss(xml):
                if n >= cfg.get("max_itens", 60) or not i["titulo"] or not i["audio"]:
                    continue
                nome, fm, corpo = monta_post(i, fonte.get("marca", "jeronimo"), "podcast")
                escreve(RAIZ / "content" / "podcast", nome, fm, corpo, rel)
                n += 1
            print(f"OK     podcast {fonte['url']}: {n} episódios")
        except Exception as e:  # noqa: BLE001
            rel["falhas"].append(f"podcast {fonte['url']}: {e}")
            print(f"AVISO  podcast {fonte['url']}: {e}")


def channel_id(fonte, baixa_url):
    if fonte.get("channel_id"):
        return fonte["channel_id"]
    pg = baixa_url(f"https://www.youtube.com/@{fonte['handle']}").decode("utf-8", "ignore")
    m = re.search(r'youtube\.com/channel/(UC[\w-]{22})', pg) or re.search(r'"(?:channelId|externalId)":"(UC[\w-]{22})"', pg)
    if not m:
        raise RuntimeError(f"não achei o channel_id de @{fonte['handle']}")
    return m.group(1)


def sync_youtube(cfg, baixa_url, rel):
    for fonte in cfg.get("youtube") or []:
        nome_fonte = fonte.get("handle") or fonte.get("channel_id")
        try:
            cid = channel_id(fonte, baixa_url)
            raiz = ET.fromstring(baixa_url(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"))
            n = 0
            for e in raiz.findall("atom:entry", NS):
                if n >= cfg.get("max_itens", 60):
                    break
                vid = txt(e, "yt:videoId")
                titulo = txt(e, "atom:title")
                if not vid or not titulo:
                    continue
                d = data_iso(txt(e, "atom:published"))
                desc = txt(e, "media:group/media:description")
                fm = {"title": titulo, "date": d.strftime("%Y-%m-%dT%H:%M:%S+00:00") if d else None,
                      "slug": f"{slugify(titulo)}-{vid[:6].lower()}", "description": resumo(desc),
                      "marca": fonte["marca"], "youtube": vid, "origem": f"https://www.youtube.com/watch?v={vid}"}
                fm = {k: v for k, v in fm.items() if v not in (None, "")}
                nome = f"{d:%Y-%m-%d}-{fm['slug']}.md" if d else f"{fm['slug']}.md"
                escreve(RAIZ / "content" / "videos", nome, fm, "", rel)
                n += 1
            print(f"OK     youtube @{nome_fonte}: {n} vídeos")
        except Exception as e:  # noqa: BLE001
            rel["falhas"].append(f"youtube @{nome_fonte}: {e}")
            print(f"AVISO  youtube @{nome_fonte}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", help="pasta com substack-HOST.xml, podcast-N.xml, youtube.xml (testes)")
    a = ap.parse_args()
    cfg = yaml.safe_load((RAIZ / "data" / "fontes.yaml").read_text(encoding="utf-8"))
    rel = {"escritos": 0, "iguais": 0, "ignorados": 0, "falhas": []}
    if a.offline:
        d = Path(a.offline)

        def xml_por_host(h):
            return (d / f"substack-{h}.xml").read_bytes()

        def baixa_url(u):
            if "youtube.com/feeds" in u:
                return (d / "youtube.xml").read_bytes()
            if "youtube.com/@" in u:
                return b'<link rel="canonical" href="https://www.youtube.com/channel/UCabcdefghijklmnopqrstuv">'
            return (d / "podcast-0.xml").read_bytes()
    else:
        def xml_por_host(h):
            return baixa(f"https://{h}/feed")
        baixa_url = baixa
    sync_substack(cfg, xml_por_host, rel)
    sync_podcasts(cfg, baixa_url, rel)
    sync_youtube(cfg, baixa_url, rel)
    print(f"Resumo: {rel['escritos']} escritos, {rel['iguais']} sem mudança, {rel['ignorados']} seus (intocados), {len(rel['falhas'])} falhas")
    total = len(cfg.get("substack", [])) + len(cfg.get("youtube") or []) + len(cfg.get("podcast_feeds") or [])
    if total and len(rel["falhas"]) == total:
        sys.exit(1)   # tudo falhou: o CI para antes de publicar uma réplica vazia por cima


if __name__ == "__main__":
    main()
