"""Upload-Paket für convocare.at/kurswert/.

Erzeugt einen Ordner mit Startseite, Offenlegung, Stylesheet und Schriften.
Die Tagesdaten und die heutige Messung kommen live von GitHub Pages,
deshalb muss das Paket nur bei Änderungen an Reise oder Rechtstext neu
hochgeladen werden.

    python -m kdw.bundle [zielordner]
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path

from .report import render_legal

PAGES = "https://thomasreincom-cmd.github.io/kurswert-der-wirklichkeit/"
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

HEUTE = f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Heutige Messung · Kurswert der Wirklichkeit</title>
<link rel="stylesheet" href="ci.css">
<style>
html,body{{margin:0;height:100%;background:var(--void,#04060f);color:var(--text,#e7f0ff);font-family:var(--body,system-ui)}}
.top{{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--glass-border,#223);font-size:14px}}
.top b{{font:700 13px var(--display,system-ui);letter-spacing:.12em}}
.top a{{color:var(--cyan,#00f0ff)}}
iframe{{display:block;width:100%;height:calc(100% - 46px);border:0}}
</style></head><body>
<div class="top"><b>KURSWERT DER WIRKLICHKEIT</b>
<a href="index.html">Zur Reise</a>
<a href="impressum.html">Offenlegung</a>
<a href="{PAGES}heute.html" target="_blank" rel="noopener">Messung in eigenem Fenster</a></div>
<iframe src="{PAGES}heute.html" title="Heutige Messung, täglich neu erzeugt"></iframe>
</body></html>"""


def build(out: Path) -> Path:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    page = (STATIC / "reise.html").read_text(encoding="utf-8")
    page = page.replace('fetch("summary.json"', f'fetch("{PAGES}summary.json"')
    assert PAGES + "summary.json" in page
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "heute.html").write_text(HEUTE, encoding="utf-8")
    (out / "impressum.html").write_text(
        render_legal(date.today().isoformat(), host="convocare"), encoding="utf-8")
    shutil.copy(STATIC / "ci.css", out / "ci.css")
    shutil.copytree(STATIC / "fonts", out / "fonts")
    zpath = out.with_suffix(".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, Path(out.name) / f.relative_to(out))
    return zpath


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist/kurswert")
    print(build(target))
