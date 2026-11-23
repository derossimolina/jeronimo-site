#!/usr/bin/env python3
"""Teste offline do sincronizar.py: python3 tests/testa_sincronizar.py"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "ferramentas"))
import sincronizar as s  # noqa: E402

# 1. limpeza de HTML
sujo = ('<div class="subscription-widget-wrap"><form><input type="email"><button>Assine</button></form></div>'
        '<script>alert(1)</script><p onclick="x()">Texto <a href="javascript:alert(1)">mau</a> '
        '<a href="https://ok.com">bom</a></p><img src="https://a/p.gif" width="1" height="1"><iframe src="x"></iframe><p>fim</p>')
limpo = s.limpa_html(sujo)
assert "script" not in limpo and "form" not in limpo and "onclick" not in limpo and "javascript:" not in limpo, limpo
assert "https://ok.com" in limpo and "<p>fim</p>" in limpo and "p.gif" not in limpo, limpo
# 2. idempotência e respeito a arquivos do usuário
tmp = Path(tempfile.mkdtemp())
rel = {"escritos": 0, "iguais": 0, "ignorados": 0, "falhas": []}
s.escreve(tmp, "a.md", {"title": "A"}, "corpo", rel)
s.escreve(tmp, "a.md", {"title": "A"}, "corpo", rel)
assert (rel["escritos"], rel["iguais"]) == (1, 1), rel
(tmp / "b.md").write_text("---\ntitle: Meu\n---\ntexto meu\n", encoding="utf-8")
s.escreve(tmp, "b.md", {"title": "Outro"}, "x", rel)
assert rel["ignorados"] == 1 and "texto meu" in (tmp / "b.md").read_text(encoding="utf-8")
# 3. leitura dos feeds de teste
r = subprocess.run([sys.executable, str(RAIZ / "ferramentas" / "sincronizar.py"), "--offline", str(RAIZ / "tests" / "fixtures")],
                   capture_output=True, text=True)
assert r.returncode == 0 and "0 falhas" in r.stdout, r.stdout + r.stderr
print("ok")
