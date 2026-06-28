#!/usr/bin/env python3
"""Generate references/fonts.html — a single page collecting every font used by
the 110 looks (and 4 styles), with source, license, and download/specimen links.

ppt-lab ships only design *tokens* (font names), never font binaries. Users
install the fonts themselves from the links below. Proprietary faces are not
redistributable and fall back to open faces (Inter / Pretendard) on render.

Run from the `references/` dir:  python3 tools/render-font-links.py
Re-run after adding looks/fonts; any unmapped font is reported and listed in an
"unclassified" box so FONTMAP can be extended.
"""
import json
import os
import sys
import html

HERE = os.path.dirname(os.path.abspath(__file__))
TOKENS = os.path.join(HERE, "..", "design-tokens.json")
OUT = os.path.join(HERE, "..", "fonts.html")

# Weight/style-only names that are really a single family at a given weight.
ALIASES = {
    "Poppins ExtraBold": "Poppins",
}


def gf(name):
    """Google Fonts specimen URL for a family name."""
    return "https://fonts.google.com/specimen/" + name.replace(" ", "+")


# category: google (OFL/Apache via Google Fonts) · korean · fontshare · system · proprietary
def _g(name, license="SIL OFL 1.1"):
    return {"category": "google", "license": license, "url": gf(name),
            "source": "Google Fonts"}


FONTMAP = {
    # ── Latin · Google Fonts (open) ──
    "Anton": _g("Anton"), "Archivo": _g("Archivo"), "Archivo Black": _g("Archivo Black"),
    "Caveat": _g("Caveat"), "Cormorant": _g("Cormorant"),
    "Cormorant Garamond": _g("Cormorant Garamond"), "Fraunces": _g("Fraunces"),
    "Fredoka": _g("Fredoka"), "Geist": _g("Geist"), "IBM Plex Mono": _g("IBM Plex Mono"),
    "IBM Plex Sans": _g("IBM Plex Sans"), "Inter": _g("Inter"),
    "Inter Tight": _g("Inter Tight"), "JetBrains Mono": _g("JetBrains Mono"),
    "Jost": _g("Jost"), "Manrope": _g("Manrope"), "Newsreader": _g("Newsreader"),
    "Nunito": _g("Nunito"), "Orbitron": _g("Orbitron"), "PT Serif": _g("PT Serif"),
    "Playfair Display": _g("Playfair Display"), "Plus Jakarta Sans": _g("Plus Jakarta Sans"),
    "Poppins": _g("Poppins"), "Quicksand": _g("Quicksand"),
    "Roboto Flex": _g("Roboto Flex"), "Saira Condensed": _g("Saira Condensed"),
    "Source Serif 4": _g("Source Serif 4"), "Space Grotesk": _g("Space Grotesk"),
    "Spectral": _g("Spectral"), "Work Sans": _g("Work Sans"),
    # ── Korean ──
    "Pretendard": {"category": "korean", "license": "SIL OFL 1.1",
                   "url": "https://github.com/orioncactus/pretendard",
                   "source": "orioncactus/pretendard",
                   "note": "기본 한글(ea) 폰트 · 미설치 시 모든 룩의 한글 폴백"},
    "Pretendard Black": {"category": "korean", "license": "SIL OFL 1.1",
                   "url": "https://github.com/orioncactus/pretendard",
                   "source": "orioncactus/pretendard",
                   "note": "Pretendard Black(900) weight · OFL 동일"},
    "Pretendard ExtraBold": {"category": "korean", "license": "SIL OFL 1.1",
                   "url": "https://github.com/orioncactus/pretendard",
                   "source": "orioncactus/pretendard",
                   "note": "Pretendard ExtraBold(800) weight · OFL 동일"},
    "MaruBuri": {"category": "korean", "license": "무료(임베딩 허용)",
                 "url": "https://hangeul.naver.com/maruburi",
                 "source": "Naver 마루 부리",
                 "note": "에디토리얼·럭셔리 세리프 룩 8종의 한글 본문"},
    "Song Myung": {"category": "korean", "license": "SIL OFL 1.1", "url": gf("Song Myung"),
                   "source": "Google Fonts (Kang Min Koo)",
                   "note": "세리프 룩 12종의 표지·헤딩(display 티어) 한글 페이스"},
    "Gowun Batang": {"category": "korean", "license": "SIL OFL 1.1", "url": gf("Gowun Batang"),
                     "source": "Google Fonts",
                     "note": "대체 디스플레이 세리프(현재 미매핑 · 변주용)"},
    # ── Fontshare ──
    "Clash Display": {"category": "fontshare", "license": "ITF Free Font License",
                      "url": "https://www.fontshare.com/fonts/clash-display",
                      "source": "Fontshare (Indian Type Foundry)"},
    # ── System (preinstalled) ──
    "Arial": {"category": "system", "license": "독점(시스템 기본)",
              "url": "", "source": "Microsoft",
              "note": "Windows/Office 기본 설치 · Linux는 Liberation Sans로 대체"},
    # ── Proprietary (재배포 불가 → 오픈 폴백) ──
    "Futura": {"category": "proprietary", "license": "독점(URW/Linotype)", "url": "",
               "source": "URW/Linotype", "note": "미설치 시 Inter로 폴백"},
    "Helvetica Neue": {"category": "proprietary", "license": "독점(Linotype)", "url": "",
                       "source": "Linotype", "note": "미설치 시 Inter로 폴백"},
    "SF Pro Display": {"category": "proprietary", "license": "Apple 라이선스(재배포 불가)",
                       "url": "https://developer.apple.com/fonts/",
                       "source": "Apple", "note": "Apple 개발자 사이트에서만 배포 · 미설치 시 Inter 폴백"},
    "Hyundai Sans Head": {"category": "proprietary", "license": "독점(브랜드 폰트)", "url": "",
                          "source": "Hyundai", "note": "비공개 브랜드 폰트 · Inter로 폴백"},
}

CAT_META = {
    "korean": ("한글 폰트", "한글(ea) 본문·디스플레이. 미설치 시 Pretendard 폴백 → 두부(▯) 없음."),
    "google": ("Google Fonts (오픈)", "SIL OFL / Apache 2.0. 각 specimen에서 'Download family'."),
    "fontshare": ("Fontshare", "ITF Free Font License — 무료, 임베딩 허용."),
    "system": ("시스템 기본", "별도 설치 불필요(OS 기본). Linux는 오픈 대체 폰트로 렌더."),
    "proprietary": ("독점 폰트 (재배포 불가)", "리포에 포함하지 않음. 라이선스가 있으면 직접 설치, 없으면 자동으로 Inter/Pretendard 오픈 폴백."),
}
CAT_ORDER = ["korean", "google", "fontshare", "system", "proprietary"]


def collect(tokens):
    """name -> set of slugs that use it (looks + styles)."""
    used = {}
    def add(name, slug):
        if not name:
            return
        used.setdefault(name, set()).add(slug)
    for slug, lk in tokens.get("looks", {}).items():
        if not isinstance(lk, dict):
            continue
        f = lk.get("fonts", {}) or {}
        if not isinstance(f, dict):
            continue
        add(f.get("latin"), slug)
        add(f.get("ea"), slug)
        d = f.get("display", {}) or {}
        if isinstance(d, dict):
            add(d.get("latin"), slug)
            add(d.get("ea"), slug)
    for key, st in tokens.get("styles", {}).items():
        if not isinstance(st, dict):
            continue
        f = st.get("fonts", {}) or {}
        if not isinstance(f, dict):
            continue
        add(f.get("latin"), "style:" + key)
        add(f.get("ea"), "style:" + key)
    return used


def main():
    tokens = json.load(open(TOKENS, encoding="utf-8"))
    used = collect(tokens)

    # resolve aliases (weight-only names fold into their family, counts merged)
    resolved = {}
    for name, slugs in used.items():
        canon = ALIASES.get(name, name)
        resolved.setdefault(canon, set()).update(slugs)

    unclassified = sorted(n for n in resolved if n not in FONTMAP)
    if unclassified:
        print("WARNING unmapped fonts (extend FONTMAP):", unclassified, file=sys.stderr)

    by_cat = {c: [] for c in CAT_ORDER}
    for name in sorted(resolved):
        info = FONTMAP.get(name)
        cat = info["category"] if info else "unclassified"
        by_cat.setdefault(cat, []).append((name, info, len(resolved[name])))

    cards = []
    for cat in CAT_ORDER + (["unclassified"] if unclassified else []):
        rows = by_cat.get(cat) or []
        if not rows:
            continue
        title, desc = CAT_META.get(cat, ("미분류", "FONTMAP에 추가 필요."))
        items = []
        for name, info, n in rows:
            info = info or {"license": "—", "url": "", "source": "—"}
            url = info.get("url") or ""
            link = (f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(url.replace("https://",""))}</a>'
                    if url else '<span class="nolink">다운로드 링크 없음</span>')
            note = info.get("note")
            note_html = f'<div class="note">{html.escape(note)}</div>' if note else ""
            items.append(f'''      <tr>
        <td class="fname">{html.escape(name)}<span class="cnt">{n}</span></td>
        <td>{html.escape(info.get("source","—"))}</td>
        <td><span class="lic">{html.escape(info.get("license","—"))}</span></td>
        <td>{link}{note_html}</td>
      </tr>''')
        cards.append(f'''  <section class="cat">
    <h2>{html.escape(title)} <span class="ncat">{len(rows)}</span></h2>
    <p class="catdesc">{html.escape(desc)}</p>
    <table>
      <thead><tr><th>폰트</th><th>출처</th><th>라이선스</th><th>다운로드 / specimen</th></tr></thead>
      <tbody>
{chr(10).join(items)}
      </tbody>
    </table>
  </section>''')

    total = len(resolved)
    doc = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ppt-lab-rebuild · 폰트 출처 ({total})</title>
<style>
  :root{{--bd:#E5E7EB;--mut:#6B7280;--ink:#111827;--accent:#2563EB}}
  *{{box-sizing:border-box}}
  body{{margin:0;font-family:-apple-system,'Pretendard',system-ui,sans-serif;color:var(--ink);background:#F9FAFB;line-height:1.5}}
  header{{padding:32px 28px 18px;border-bottom:1px solid var(--bd);background:#fff}}
  h1{{margin:0 0 6px;font-size:22px}}
  header p{{margin:4px 0;color:var(--mut);font-size:13px;max-width:760px}}
  main{{padding:8px 28px 64px;max-width:980px}}
  .cat{{margin-top:30px}}
  h2{{font-size:16px;margin:0 0 4px;display:flex;align-items:center;gap:8px}}
  .ncat{{font-size:11px;background:#EEF2FF;color:#3730A3;border-radius:10px;padding:1px 8px;font-weight:600}}
  .catdesc{{margin:0 0 10px;color:var(--mut);font-size:12.5px}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--bd);border-radius:10px;overflow:hidden;font-size:13px}}
  th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--bd);vertical-align:top}}
  th{{background:#F3F4F6;font-size:11.5px;color:var(--mut);font-weight:600;text-transform:uppercase;letter-spacing:.03em}}
  tr:last-child td{{border-bottom:none}}
  .fname{{font-weight:600;white-space:nowrap}}
  .cnt{{font-weight:400;color:var(--mut);font-size:11px;margin-left:7px}}
  .cnt::before{{content:"룩 "}}
  .lic{{font-size:11.5px;background:#F3F4F6;border-radius:6px;padding:2px 7px;color:#374151}}
  a{{color:var(--accent);text-decoration:none;word-break:break-all}}
  a:hover{{text-decoration:underline}}
  .nolink{{color:#9CA3AF;font-size:12px}}
  .note{{color:var(--mut);font-size:11.5px;margin-top:3px}}
</style></head>
<body>
<header>
  <h1>ppt-lab-rebuild — 폰트 출처 & 다운로드</h1>
  <p>이 하네스는 디자인 <b>토큰(폰트 이름)</b>만 배포합니다. 폰트 파일은 포함하지 않으니 아래 출처에서 직접 받으세요. 한글 폰트가 없으면 Pretendard, 라틴 독점 폰트가 없으면 Inter로 자동 폴백되어 빌드는 항상 성공합니다(두부 깨짐 없음).</p>
  <p>총 {total}종 · 라이선스는 각 배포처 기준이며 변경될 수 있으니 설치 전 확인하세요. 자세한 라이선스 고지는 <code>THIRD-PARTY-NOTICES.md</code> 참조.</p>
</header>
<main>
{chr(10).join(cards)}
</main>
</body></html>'''
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"[fonts] {total} fonts -> {os.path.normpath(OUT)} ({len(doc)} bytes)")
    if unclassified:
        print(f"[fonts] {len(unclassified)} UNCLASSIFIED (see warning above)")


if __name__ == "__main__":
    main()
