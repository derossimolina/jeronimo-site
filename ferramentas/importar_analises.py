#!/usr/bin/env python3
"""Leva as análises escritas no Obsidian para content/analises/.

Roda só no computador de quem escreve (o CI não enxerga o cofre). Lê a pasta de análises
do cofre sem alterar nada nela e só considera as notas com `publicar: true` nas propriedades.

Regras:
  - Prévia por padrão: mostra o que seria gravado. Só grava com --gravar.
  - Barra a nota inteira se faltar campo da ficha, se um fato vier sem link ou sem data, se a
    probabilidade ou o horizonte estiverem fora da escala (data/escalas.yaml), se o tema for um
    rótulo proibido, se o texto usar um termo vetado ou se uma imagem vier sem texto alternativo.
  - Só cria ou atualiza arquivos com `importado: true` no front matter. Arquivo sem essa marca é
    escrito à mão: o script nunca toca nele. O sincronizar.py também não toca nestes arquivos.
  - Nunca apaga nada. Análise que deixou de ter `publicar: true` aparece no relatório.
  - Nome de nota, caminho e comentários do cofre (%% ... %%) e callouts (> [!...]) não vão para o site.

Uso:
  py -3.12 ferramentas/importar_analises.py                       # prévia
  py -3.12 ferramentas/importar_analises.py --gravar              # grava
  py -3.12 ferramentas/importar_analises.py --origem PASTA --anexos PASTA --saida PASTA   (testes)
"""
import argparse, re, shutil, sys, unicodedata
from datetime import date, datetime
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM_PADRAO = Path("D:/Notas/21 Conteúdo/Análises")
ANEXOS_PADRAO = Path("D:/Notas/92 Anexos")
ESCALAS = yaml.safe_load((RAIZ / "data" / "escalas.yaml").read_text(encoding="utf-8"))

# Títulos do corpo que viram blocos da ficha. O resto do corpo é o texto da análise.
BLOCOS = {
    "o que aconteceu": "fatos",
    "minha leitura": "leitura",
    "probabilidade e horizonte": "probabilidade_texto",
    "o que observar": "sinais",
    "quem é afetado": "afetados",
    "correções": "correcoes",
}
ROTULOS_PROIBIDOS = {"posição", "opinião", "fato", "análise", "hipótese"}
# Design system 5.6: termos que não entram em peça da marca.
VETADOS = [
    r"liberal[- ]progressista", r"bolsonarismo", r"lulopetismo",
    r"pelo empres[aá]rio", r"n[oó]s,? empres[aá]rios",
]
# Não barram, mas aparecem no relatório para conferência.
AVISOS = [r"\bsebrae\b", r"\buninter\b", r"governo do rs", r"\bfsqca\b", r"\btese\b"]

DATA_BR = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
LINK_MD = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
WIKILINK = re.compile(r"(?<!!)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")
EMBED = re.compile(r"!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
IMG_MD = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
IMAGEM = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}


class NotaInvalida(Exception):
    pass


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80]


def le_nota(f):
    texto = f.read_text(encoding="utf-8")
    if not texto.startswith("---"):
        return {}, texto
    partes = texto.split("---", 2)
    if len(partes) < 3:
        return {}, texto
    fm = yaml.safe_load(partes[1]) or {}
    return (fm if isinstance(fm, dict) else {}), partes[2]


def data_iso(v, campo):
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v or "").strip()
    m = DATA_BR.fullmatch(s)
    if m:
        d, mth, a = map(int, m.groups())
        return date(a, mth, d).isoformat()
    try:
        return date.fromisoformat(s[:10]).isoformat()
    except ValueError:
        raise NotaInvalida(f"{campo}: data inválida ({s!r}); use AAAA-MM-DD ou DD/MM/AAAA")


def limpa_obsidian(md):
    md = re.sub(r"%%.*?%%", "", md, flags=re.S)                       # comentários
    linhas, saida, em_callout = md.splitlines(), [], False
    for ln in linhas:                                                  # callouts inteiros
        if re.match(r"^\s*>\s*\[!", ln):
            em_callout = True
            continue
        if em_callout and ln.lstrip().startswith(">"):
            continue
        em_callout = False
        saida.append(ln)
    return "\n".join(saida)


def separa_blocos(corpo):
    """Divide o corpo pelos títulos de nível 2. Devolve (blocos da ficha, texto restante)."""
    blocos, resto, atual = {}, [], None
    for ln in corpo.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            chave = BLOCOS.get(m.group(1).strip().lower())
            atual = chave
            if chave:
                blocos[chave] = []
                continue
        if re.match(r"^#\s+", ln):          # o H1 do Obsidian não vai: o título vem das propriedades
            continue
        (blocos[atual] if atual else resto).append(ln)
    return {k: "\n".join(v).strip() for k, v in blocos.items()}, "\n".join(resto).strip()


def itens(bloco):
    return [re.sub(r"^\s*[-*]\s+", "", ln).strip() for ln in bloco.splitlines() if re.match(r"^\s*[-*]\s+\S", ln)]


def parse_fato(linha):
    links = LINK_MD.findall(linha)
    datas = DATA_BR.findall(linha)
    if not links or not datas:
        raise NotaInvalida(f"fato sem {'link' if not links else 'data (DD/MM/AAAA)'}: {linha[:90]!r}")
    fonte, url = links[-1]
    d, m, a = map(int, datas[-1])
    texto = linha[: linha.rfind("[" + fonte + "]")]
    texto = re.sub(r"[\s—–\-:,(]*(fonte\s*:?)?\s*$", "", texto, flags=re.I).strip()
    if not texto:
        raise NotaInvalida(f"fato sem texto antes da fonte: {linha[:90]!r}")
    return {"texto": texto, "fonte": fonte, "url": url, "data": date(a, m, d).isoformat()}


def parse_correcao(linha):
    m = re.match(r"^(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\s*[:—–-]\s*(.+)$", linha)
    if not m:
        raise NotaInvalida(f"correção deve começar pela data: {linha[:90]!r}")
    return {"data": data_iso(m.group(1), "correção"), "texto": m.group(2).strip()}


def acha_anexo(nome, anexos, origem):
    for base in (origem, anexos):
        if base and base.exists():
            achados = [p for p in base.rglob(Path(nome).name) if p.is_file()]
            if achados:
                return achados[0]
    raise NotaInvalida(f"imagem não encontrada no cofre: {nome}")


def converte(md, slug, publicadas, anexos, origem, copias):
    """Wikilinks, imagens do cofre e chaves do Hugo. `copias` recebe (origem, destino relativo)."""
    def embed(m):
        nome, alt = m.group(1).strip(), (m.group(2) or "").strip()
        if Path(nome).suffix.lower() not in IMAGEM:
            raise NotaInvalida(f"incorporação que não é imagem: ![[{nome}]]")
        if not alt or alt.isdigit() or re.fullmatch(r"\d+x\d+", alt):
            raise NotaInvalida(f"imagem sem texto alternativo: ![[{nome}]] (use ![[{nome}|descrição]])")
        arq = acha_anexo(nome, anexos, origem)
        destino = f"{slug}/{slugify(arq.stem)}{arq.suffix.lower()}"
        copias.append((arq, destino))
        return f"![{alt}](/analises/{destino})"

    def img_md(m):
        alt, src = m.group(1).strip(), m.group(2)
        if not alt:
            raise NotaInvalida(f"imagem sem texto alternativo: {src}")
        if src.startswith("https://"):
            return m.group(0)
        if src.startswith("http://"):
            raise NotaInvalida(f"imagem por http (use https): {src}")
        return embed(re.match(EMBED, f"![[{Path(src).name}|{alt}]]"))

    def wiki(m):
        alvo, rotulo = m.group(1).strip(), (m.group(2) or m.group(1)).strip()
        if alvo in publicadas:
            return f"[{rotulo}](/analises/{publicadas[alvo]}/)"
        return rotulo                       # nota não publicada: só o texto, sem o nome do cofre

    md = IMG_MD.sub(img_md, md)             # antes do EMBED: a saída do embed também é ![alt](...)
    md = EMBED.sub(embed, md)
    md = WIKILINK.sub(wiki, md)
    return md.replace("{{", "{&#123;")      # o Hugo não executa shortcode vindo da nota


def confere_termos(texto, onde):
    for p in VETADOS:
        m = re.search(p, texto, re.I)
        if m:
            raise NotaInvalida(f"termo vetado pelo design system (5.6) em {onde}: {m.group(0)!r}")
    return [re.search(p, texto, re.I).group(0) for p in AVISOS if re.search(p, texto, re.I)]


def monta(f, fm, corpo, publicadas, anexos, origem):
    for campo in ("title", "date", "tema", "secao", "resumo", "horizonte", "probabilidade"):
        if not str(fm.get(campo) or "").strip():
            raise NotaInvalida(f"falta a propriedade `{campo}`")
    tema = str(fm["tema"]).strip()
    if tema.lower() in ROTULOS_PROIBIDOS:
        raise NotaInvalida(f"tema {tema!r} é rótulo proibido; use o assunto (ex.: Política fiscal)")
    for campo in ("secao", "horizonte", "probabilidade"):
        if str(fm[campo]).strip() not in ESCALAS[campo]:
            raise NotaInvalida(f"`{campo}` deve ser um de: {', '.join(ESCALAS[campo])}")
    slug = slugify(str(fm.get("slug") or fm["title"]))
    corpo = limpa_obsidian(corpo)
    blocos, texto = separa_blocos(corpo)
    fatos = [parse_fato(x) for x in itens(blocos.get("fatos", ""))]
    if not fatos:
        raise NotaInvalida("o bloco `## O que aconteceu` precisa de ao menos um fato com fonte e data")
    if not blocos.get("leitura"):
        raise NotaInvalida("falta o bloco `## Minha leitura`")
    copias = []
    conv = lambda s: converte(s, slug, publicadas, anexos, origem, copias)  # noqa: E731
    saida = {
        "title": str(fm["title"]).strip(),
        "date": data_iso(fm["date"], "date"),
        "slug": slug,
        "description": str(fm["resumo"]).strip(),
        "tema": tema,
        "secao": str(fm["secao"]).strip(),
        "resumo": str(fm["resumo"]).strip(),
        "fatos": [{**x, "texto": conv(x["texto"])} for x in fatos],
        "leitura": conv(blocos["leitura"]),
        "horizonte": str(fm["horizonte"]).strip(),
        "probabilidade": str(fm["probabilidade"]).strip(),
    }
    if blocos.get("probabilidade_texto"):
        saida["probabilidade_texto"] = conv(blocos["probabilidade_texto"])
    for chave in ("sinais", "afetados"):
        lista = [conv(x) for x in itens(blocos.get(chave, ""))]
        if lista:
            saida[chave] = lista
    if fm.get("atualizado_em"):
        saida["atualizado_em"] = data_iso(fm["atualizado_em"], "atualizado_em")
    corr = [parse_correcao(x) for x in itens(blocos.get("correcoes", ""))]
    if corr:
        saida["correcoes"] = corr
    if fm.get("imagem"):
        saida["imagem"] = str(fm["imagem"])
    saida["importado"] = True
    texto = conv(texto)
    avisos = confere_termos(yaml.safe_dump(saida, allow_unicode=True) + texto, f.name)
    if len(saida["resumo"]) > 320:
        avisos.append(f"resumo com {len(saida['resumo'])} caracteres (o ideal é até 3 linhas, ~320)")
    return slug, saida, texto, copias, avisos


def eh_importado(texto):
    fm, _ = le_nota_texto(texto)
    return fm.get("importado") is True


def le_nota_texto(texto):
    if not texto.startswith("---"):
        return {}, texto
    partes = texto.split("---", 2)
    if len(partes) < 3:
        return {}, texto
    try:
        fm = yaml.safe_load(partes[1]) or {}
    except yaml.YAMLError:
        return {}, texto
    return (fm if isinstance(fm, dict) else {}), partes[2]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origem", type=Path, default=ORIGEM_PADRAO)
    ap.add_argument("--anexos", type=Path, default=ANEXOS_PADRAO)
    ap.add_argument("--saida", type=Path, default=RAIZ, help="raiz do site (testes usam uma pasta temporária)")
    ap.add_argument("--gravar", action="store_true", help="grava os arquivos; sem isso, só mostra a prévia")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):          # console do Windows (cp1252) não imprime acento nem seta
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not a.origem.is_dir():
        print(f"ERRO   pasta de análises não encontrada: {a.origem}")
        return 2
    conteudo, estatico = a.saida / "content" / "analises", a.saida / "static" / "analises"
    notas = []
    for f in sorted(a.origem.rglob("*.md")):
        try:
            fm, corpo = le_nota(f)
        except yaml.YAMLError as e:
            print(f"ERRO   {f.name}: propriedades ilegíveis ({e.__class__.__name__})")
            continue
        if fm.get("publicar") is True:
            notas.append((f, fm, corpo))
    publicadas = {f.stem: slugify(str(fm.get("slug") or fm.get("title") or f.stem)) for f, fm, _ in notas}
    # Primeira passada: link interno só para nota que passa na validação (senão o link quebraria).
    for f, fm, corpo in notas:
        try:
            monta(f, fm, corpo, publicadas, a.anexos, a.origem)
        except NotaInvalida:
            publicadas.pop(f.stem, None)

    rel = {"novas": 0, "atualizadas": 0, "iguais": 0, "barradas": 0, "protegidas": 0}
    gerados = set()
    for f, fm, corpo in notas:
        try:
            slug, saida, texto, copias, avisos = monta(f, fm, corpo, publicadas, a.anexos, a.origem)
        except NotaInvalida as e:
            rel["barradas"] += 1
            print(f"BARRADA {f.name}: {e}")
            continue
        gerados.add(slug)
        alvo = conteudo / f"{slug}.md"
        novo = "---\n" + yaml.safe_dump(saida, allow_unicode=True, sort_keys=False, width=1000) + "---\n\n" + texto + "\n"
        atual = alvo.read_text(encoding="utf-8") if alvo.exists() else None
        if atual is not None and not eh_importado(atual):
            rel["protegidas"] += 1
            print(f"IGNORADA {f.name}: content/analises/{slug}.md foi escrito à mão (sem `importado: true`)")
            continue
        estado = "iguais" if atual == novo else ("atualizadas" if atual else "novas")
        rel[estado] += 1
        for av in avisos:
            print(f"AVISO  {f.name}: confira {av!r}")
        print(f"{'OK    ' if estado == 'iguais' else 'GRAVA ' if a.gravar else 'PRÉVIA'} {f.name} → content/analises/{slug}.md"
              f" ({estado}, {len(saida['fatos'])} fatos, {len(copias)} imagens)")
        if a.gravar and estado != "iguais":
            conteudo.mkdir(parents=True, exist_ok=True)
            alvo.write_text(novo, encoding="utf-8")
        if a.gravar:
            for arq, destino in copias:
                d = estatico / destino
                d.parent.mkdir(parents=True, exist_ok=True)
                if not d.exists() or d.read_bytes() != arq.read_bytes():
                    shutil.copyfile(arq, d)

    if conteudo.exists():
        for f in sorted(conteudo.glob("*.md")):
            if f.stem not in gerados and not f.name.startswith("_") and eh_importado(f.read_text(encoding="utf-8")):
                print(f"AVISO  content/analises/{f.name} não tem mais nota com `publicar: true`. Nada foi apagado.")

    print(f"\n{len(notas)} notas para publicar: {rel['novas']} novas, {rel['atualizadas']} atualizadas, "
          f"{rel['iguais']} iguais, {rel['barradas']} barradas, {rel['protegidas']} protegidas."
          + ("" if a.gravar else " Prévia: nada foi gravado (use --gravar)."))
    return 1 if rel["barradas"] else 0


if __name__ == "__main__":
    sys.exit(main())
