from __future__ import annotations

import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SOURCES = os.path.join(ROOT, "assets", "audio", "sfx", "sources.json")
CREDITS = os.path.join(ROOT, "CREDITS.md")
BEGIN, END = "<!-- sfx:inicio (gerado por tools/audio/credits_sfx.py) -->", "<!-- sfx:fim -->"
SITE = {"freesound": "Freesound", "kenney": "Kenney", "opengameart": "OpenGameArt", "mixkit": "Mixkit"}
LICENSE_URL = {
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "Mixkit Sound Effects Free License": "https://mixkit.co/license/",
}


def rows() -> list[dict]:
    data = json.load(open(SOURCES, encoding="utf-8"))
    merged: dict[str, dict] = {}
    for sid, e in sorted(data.items()):
        key = e["url"] + "|" + e["title"]
        if key in merged:
            merged[key]["ids"].append(sid)
        else:
            merged[key] = dict(e, ids=[sid])
    return sorted(merged.values(), key=lambda e: (e["license"] != "CC0", e["ids"][0]))


def markdown() -> str:
    out = [BEGIN, "", "| Som no jogo | Original | Autor | Fonte | Licença |", "|---|---|---|---|---|"]
    for e in rows():
        where = SITE[e["source"]] + (" (%s)" % e["pack"] if "pack" in e else "")
        out.append("| %s | [%s](%s) | %s | %s | [%s](%s) |" % (
            ", ".join("`%s`" % i for i in e["ids"]), e["title"].replace("|", "/"), e["url"], e["author"], where,
            e["license"], LICENSE_URL.get(e["license"], e["url"])))
    out += ["", "Alterações feitas em todos: corte do silêncio inicial (ou ciclo com fusão de 1,5 s nos ambientes), "
            "volume ajustado ao do som sintetizado que substituiu e conversão para mono nos efeitos curtos. "
            "Os de Freesound partem da prévia OGG de alta qualidade do site.", "", END]
    return "\n".join(out)


def tex_escape(s: str) -> str:
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")):
        s = s.replace(a, b)
    return s


def latex() -> str:
    out = [r"% Gerado por tools/audio/credits_sfx.py (precisa de \usepackage{longtable} e \usepackage{hyperref})",
           r"\begin{longtable}{p{3.2cm}p{4.6cm}p{2.6cm}p{2.2cm}p{2.4cm}}",
           r"\caption{Efeitos sonoros de terceiros usados no jogo}\label{tab:sfx-creditos}\\",
           r"\hline Som no jogo & Original & Autor & Fonte & Licença \\ \hline \endfirsthead",
           r"\hline Som no jogo & Original & Autor & Fonte & Licença \\ \hline \endhead"]
    for e in rows():
        where = SITE[e["source"]] + (" (%s)" % e["pack"] if "pack" in e else "")
        out.append(r"%s & \href{%s}{%s} & %s & %s & %s \\" % (
            ", ".join(r"\texttt{%s}" % tex_escape(i) for i in e["ids"]), e["url"], tex_escape(e["title"]),
            tex_escape(e["author"]), tex_escape(where), tex_escape(e["license"].replace(" Sound Effects Free License", ""))))
    out.append(r"\hline \end{longtable}")
    return "\n".join(out) + "\n"


def main() -> None:
    if "--tex" in sys.argv:
        path = sys.argv[sys.argv.index("--tex") + 1]
        open(path, "w", encoding="utf-8").write(latex())
        print("tabela LaTeX:", path)
        return
    text = open(CREDITS, encoding="utf-8").read()
    block = markdown()
    if BEGIN in text:
        text = text[: text.index(BEGIN)] + block + text[text.index(END) + len(END):]
    else:
        text = text.rstrip("\n") + "\n\n## Efeitos sonoros\n\n" + block + "\n"
    open(CREDITS, "w", encoding="utf-8").write(text)
    print("CREDITS.md: %d sons" % len(rows()))


if __name__ == "__main__":
    main()
