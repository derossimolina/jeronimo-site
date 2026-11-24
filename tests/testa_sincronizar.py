#!/usr/bin/env python3
"""Testes offline da replicação: python3 tests/testa_sincronizar.py
Nada aqui escreve em content/: a saída vai para uma pasta temporária."""
import subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "ferramentas"))
import sincronizar as s  # noqa: E402
from limpeza import limpa_html  # noqa: E402

# 1. limpeza de HTML
sujo = ('<div class="subscription-widget-wrap"><form><input type="email"><button>Assine</button></form></div>'
        '<script>alert(1)</script><p onclick="x()">Texto <a href="javascript:alert(1)">mau</a> '
        '<a href="https://ok.com">bom</a></p><img src="https://a/p.gif" width="1" height="1"><iframe src="x"></iframe><p>fim</p>')
limpo = limpa_html(sujo)
assert "script" not in limpo and "form" not in limpo and "onclick" not in limpo and "javascript:" not in limpo, limpo
assert "https://ok.com" in limpo and "<p>fim</p>" in limpo and "p.gif" not in limpo, limpo

# 1b. vetores que a versão anterior deixava passar
assert "//evil" not in limpa_html('<a href="//evil.example/x">a</a>'), "link protocol-relative"
assert "<img" not in limpa_html('<img src="httpx:foo">') and "<img" not in limpa_html('<img src="data:image/png;base64,AA">')
assert "{{" not in limpa_html("{{< ref \"x\" >}} {{% y %}}"), "shortcode do Hugo"
assert "<script" not in limpa_html('<svg><script>alert(1)</script></svg>')
assert "<style" not in limpa_html("<style>a{}</style>texto")
# elemento descartado aninhado e mal fechado não pode engolir o resto do post
assert limpa_html("<form><div>x<form>y</div>z</form><p>resto</p>").endswith("<p>resto</p>")
# tags permitidas abertas e nunca fechadas não vazam para o layout
assert limpa_html("<p>a <a href='https://x.com'>b").count("</") == 2
assert limpa_html("<div><p>um</div><p>dois</p>") == "<p>um</p><p>dois</p>"

# 2. idempotência e respeito a arquivos do usuário
tmp = Path(tempfile.mkdtemp())
rel = {"escritos": 0, "iguais": 0, "ignorados": 0, "falhas": []}
s.escreve(tmp, "a.md", {"title": "A"}, "corpo", rel)
s.escreve(tmp, "a.md", {"title": "A"}, "corpo", rel)
assert (rel["escritos"], rel["iguais"]) == (1, 1), rel
(tmp / "b.md").write_text("---\ntitle: Meu\n---\ntexto meu\n", encoding="utf-8")
s.escreve(tmp, "b.md", {"title": "Outro"}, "x", rel)
# "gerado: true" no corpo ou no título não faz um arquivo do usuário virar sobrescrevível
(tmp / "c.md").write_text("---\ntitle: 'gerado: true'\n---\ngerado: true\n", encoding="utf-8")
s.escreve(tmp, "c.md", {"title": "Outro"}, "x", rel)
# arquivo sem front matter também é do usuário (antes: IndexError derrubava a fonte inteira)
(tmp / "d.md").write_text("só texto\n", encoding="utf-8")
s.escreve(tmp, "d.md", {"title": "Outro"}, "x", rel)
assert rel["ignorados"] == 3 and "texto meu" in (tmp / "b.md").read_text(encoding="utf-8"), rel

# 3. só https e leitura dos feeds de teste, sem tocar em content/
for url in ("http://x.com/feed", "file:///etc/passwd"):
    try:
        s.baixa(url)
    except RuntimeError:
        pass
    else:
        raise AssertionError(f"baixa aceitou {url}")
saida = Path(tempfile.mkdtemp())
r = subprocess.run([sys.executable, str(RAIZ / "ferramentas" / "sincronizar.py"), "--offline", str(RAIZ / "tests" / "fixtures"),
                    "--saida", str(saida)], capture_output=True, text=True)
assert r.returncode == 0 and "0 falhas" in r.stdout, r.stdout + r.stderr
assert any(saida.rglob("*.md")), "nada foi escrito na pasta de saída"
print("ok")
