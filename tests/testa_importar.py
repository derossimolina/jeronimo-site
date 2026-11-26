#!/usr/bin/env python3
"""Testes offline da importação do Obsidian: python3 tests/testa_importar.py
Nada aqui lê o cofre real nem escreve em content/: a saída vai para uma pasta temporária."""
import contextlib, io, sys, tempfile
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "ferramentas"))
import importar_analises as imp  # noqa: E402

FIX = RAIZ / "tests" / "fixtures" / "obsidian"


def roda(*args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cod = imp.main(["--origem", str(FIX / "Análises"), "--anexos", str(FIX / "92 Anexos"), *args])
    return cod, buf.getvalue()


# 1. prévia não grava nada
saida = Path(tempfile.mkdtemp())
cod, out = roda("--saida", str(saida))
assert not (saida / "content").exists(), "a prévia gravou arquivos"
assert "Prévia: nada foi gravado" in out, out

# 2. gravação: nota válida entra, inválida é barrada, rascunho é ignorado
cod, out = roda("--saida", str(saida), "--gravar")
assert cod == 1, "nota barrada deveria dar código 1"
assert "BARRADA Outra análise.md" in out, out
arq = saida / "content" / "analises" / "regra-fiscal-no-municipio-teste.md"
assert arq.exists(), out
txt = arq.read_text(encoding="utf-8")
fm = yaml.safe_load(txt.split("---", 2)[1])
assert fm["importado"] is True and fm["tema"] == "Política fiscal" and fm["probabilidade"] == "media"
assert fm["date"] == "2026-11-20" and fm["atualizado_em"] == "2026-11-21"
assert fm["fatos"][0] == {"texto": "A câmara aprovou a lei de teste.", "fonte": "Diário Oficial",
                          "url": "https://example.org/do", "data": "2026-11-12"}, fm["fatos"][0]
assert fm["fatos"][1]["texto"] == "Segundo fato.", fm["fatos"][1]
assert fm["correcoes"] == [{"data": "2026-11-22", "texto": "corrigido o número da lei."}]
assert fm["sinais"] == ["Votação do orçamento"] and fm["afetados"] == ["Fornecedores do município"]
corpo = txt.split("---", 2)[2]
# nada do cofre vaza: callout, comentário, nome de nota não publicada, H1
assert "Rascunho interno" not in txt and "comentário privado" not in txt and "[[" not in txt, corpo
assert "Nota privada do cofre" in corpo and "](/" not in corpo.split("Nota privada")[0][-5:]
assert "# Regra fiscal" not in corpo
# nota barrada não vira link; imagem copiada com alt
assert "link interno" in corpo and "/analises/outra/" not in corpo  # alvo foi barrado: vira só texto
assert "![Gráfico de barras de teste](/analises/regra-fiscal-no-municipio-teste/grafico-teste.png)" in corpo, corpo
assert (saida / "static" / "analises" / "regra-fiscal-no-municipio-teste" / "grafico-teste.png").exists()
assert "{{" not in txt, "chaves do Hugo não foram neutralizadas"

# 3. idempotência
cod, out = roda("--saida", str(saida), "--gravar")
assert "1 iguais" in out, out

# 4. arquivo escrito à mão nunca é sobrescrito
arq.write_text("---\ntitle: Meu\n---\ntexto meu\n", encoding="utf-8")
cod, out = roda("--saida", str(saida), "--gravar")
assert "IGNORADA" in out and "texto meu" in arq.read_text(encoding="utf-8"), out

# 5. validações unitárias
for linha, erro in (("Fato sem link, 12/11/2026", "link"), ("Fato [F](https://x.org) sem data", "data")):
    try:
        imp.parse_fato(linha)
    except imp.NotaInvalida as e:
        assert erro in str(e), e
    else:
        raise AssertionError(f"aceitou: {linha}")
try:
    imp.confere_termos("uma lente liberal-progressista", "x")
except imp.NotaInvalida:
    pass
else:
    raise AssertionError("termo vetado passou")
try:
    imp.converte("![[a.png|300]]", "s", {}, FIX, FIX, [])
except imp.NotaInvalida as e:
    assert "texto alternativo" in str(e)
else:
    raise AssertionError("imagem sem alt passou")
print("ok")
