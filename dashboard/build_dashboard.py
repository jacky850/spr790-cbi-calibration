"""
build_dashboard.py — assemble the single-file dashboard docs/index.html
(template.html + cbi_core.js + data.json), served by GitHub Pages from /docs.

Run:  python dashboard/export_data.py && python dashboard/build_dashboard.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "index.html"

html = (HERE / "template.html").read_text()
core = (HERE / "cbi_core.js").read_text()
data = (HERE / "data.json").read_text().replace("</", "<\\/")
html = html.replace("/*__CBI_CORE__*/", core).replace("/*__DATA__*/", data)
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(html)
(OUT.parent / ".nojekyll").write_text("")
print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
