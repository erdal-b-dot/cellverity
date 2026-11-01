"""KULLANIM_KILAVUZU.md → kilavuz.html (programın Yardım menüsünden açılır; tek dosya, internetsiz)."""
import re
import unicodedata
from pathlib import Path

import markdown

TR = str.maketrans("ıİşŞğĞçÇöÖüÜ", "iIsSgGcCoOuU")


def slugify(value, separator="-"):
    v = unicodedata.normalize("NFKD", value.translate(TR)).encode("ascii", "ignore").decode()
    v = re.sub(r"[^\w\s-]", "", v).strip().lower()
    return re.sub(r"[\s-]+", separator, v)


CSS = """
:root{--bg:#fff;--fg:#1d1f23;--muted:#5b6170;--line:#e3e5ea;--code:#f4f5f7;--accent:#2f7d32;--warn:#a15c00}
@media (prefers-color-scheme:dark){:root{--bg:#16181c;--fg:#e6e7ea;--muted:#a2a7b3;--line:#2c3038;--code:#22252b;--accent:#7fca7f;--warn:#e0a24a}}
html{background:var(--bg)}body{max-width:920px;margin:0 auto;padding:24px 16px 80px;background:var(--bg);color:var(--fg);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
h1{font-size:1.9em;border-bottom:2px solid var(--accent);padding-bottom:.3em}h2{margin-top:2.2em;border-bottom:1px solid var(--line);padding-bottom:.2em}
h3{margin-top:1.6em}a{color:var(--accent)}code{background:var(--code);padding:.1em .35em;border-radius:4px;font-size:.92em}
pre{background:var(--code);padding:12px;border-radius:6px;overflow-x:auto}pre code{padding:0}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.94em;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 9px;vertical-align:top;text-align:left}th{background:var(--code)}
blockquote{margin:1em 0;padding:.6em 1em;border-left:4px solid var(--warn);background:var(--code);border-radius:0 6px 6px 0}
hr{border:0;border-top:1px solid var(--line);margin:2em 0}
@media print{:root{--bg:#fff;--fg:#000;--muted:#444;--line:#bbb;--code:#f2f2f2;--accent:#1f5f22;--warn:#8a5000}
body{max-width:none;font-size:10.5pt;padding:0}a{color:inherit;text-decoration:none}h2{break-before:page}
h1+p+hr+h2{break-before:avoid}table{display:table;break-inside:auto}tr,blockquote,pre{break-inside:avoid}
@page{size:A4;margin:16mm 14mm}}
"""


GUIDES = {"tr": ("KULLANIM_KILAVUZU.md", "kilavuz.html", "KULLANIM_KILAVUZU.pdf", "ICC CTCF Ölçer Kılavuzu"),
          "en": ("USER_GUIDE.md", "user_guide.html", "USER_GUIDE.pdf", "ICC CTCF Ölçer User Guide")}


def build(lang="tr"):
    here = Path(__file__).parent
    src, html_name, _, title = GUIDES[lang]
    md = (here / src).read_text(encoding="utf-8")
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"],
                             extension_configs={"toc": {"slugify": slugify}})
    html = (f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{title}</title><style>{CSS}</style></head><body>{body}</body></html>")
    (here / html_name).write_text(html, encoding="utf-8")
    ids = set(re.findall(r'id="([^"]+)"', html))
    broken = sorted({h for h in re.findall(r'href="#([^"]+)"', html) if h not in ids})
    return len(html), broken


def build_pdf(lang="tr") -> Path | None:
    """<kılavuz>.html → <kılavuz>.pdf (Chrome/Edge başsız yazdırma; yoksa atlanır)."""
    import shutil
    import subprocess
    here = Path(__file__).parent
    for exe in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                shutil.which("google-chrome") or "", shutil.which("chromium") or "",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"):
        if exe and Path(exe).exists():
            _, html_name, pdf_name, _ = GUIDES[lang]
            out = here / pdf_name
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            "--force-prefers-color-scheme=light", f"--print-to-pdf={out}",
                            (here / html_name).resolve().as_uri()],
                           check=True, capture_output=True, timeout=120)
            return out
    return None


if __name__ == "__main__":
    for lang in GUIDES:
        n, broken = build(lang)
        print(f"{GUIDES[lang][1]}: {n // 1024} KB; kırık iç bağlantı: {broken or 'yok'}")
        pdf = build_pdf(lang)
        print(f"  PDF: {pdf.name} ({pdf.stat().st_size // 1024} KB)" if pdf else "  PDF: Chrome/Edge bulunamadı, atlandı")
