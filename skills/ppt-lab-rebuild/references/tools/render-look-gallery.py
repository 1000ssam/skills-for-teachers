#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render-look-gallery.py — design-tokens.json(looks) → look-gallery.html (자동 생성)

룩 선택 게이트용 비주얼 갤러리. 각 룩의 실제 토큰(accent/navy/canvas + 폰트 + 다크여부)
으로 HTML/CSS 미니 슬라이드 목업을 즉석 렌더한다. 손으로 고치지 말 것 — 토큰에서 매번
다시 찍어낸다(drift 0). PPTX COM 렌더가 아니라 토큰 목업이므로 즉시·경량·항상 최신.

표시: 미니 슬라이드(canvas 배경 · eyebrow · 제목(룩 폰트) · accent 바 · 차트 램프 바)
      + 룩명 · 폰트 · accent/navy/canvas 스와치 · PPT/WEB·라이트/다크·PREMIUM 배지.
필터: 트랙(전체/PPT/WEB) · 톤(전체/라이트/다크) · 이름·폰트 검색.

Usage:
  python3 render-look-gallery.py            # references/look-gallery.html 갱신
  python3 render-look-gallery.py --track ppt   # ppt 룩만(기본 필터 프리셋)
"""
import json, os, sys, html

REF = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOK = json.load(open(os.path.join(REF, "design-tokens.json"), encoding="utf-8"))
BASE = TOK["colors"]
LOOKS = TOK.get("looks", {})


def _resolve(token, pal, _depth=0):
    """룩 팔레트 우선 → base 별칭 해소 → #hex. 엔진 _resolve와 동일 의미."""
    v = pal.get(token, BASE.get(token, token))
    if isinstance(v, str) and not v.startswith("#") and _depth < 8:
        if v in pal or v in BASE:
            return _resolve(v, pal, _depth + 1)
    return v if isinstance(v, str) and v.startswith("#") else "#000000"


def _lum(hexv):
    h = hexv.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return 1.0

    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _chart_ramp(pal):
    """엔진 chart_color와 동일: accents 우선 → primary 틴트 패딩."""
    accents = pal.get("accents", ["blue", "orange"])
    pad = ["blue-light", "blue-2", "blue-pale"]
    toks = list(accents) + pad
    return [_resolve(t, pal) for t in toks[:4]]


def look_view(slug, lk):
    pal = lk.get("palette", {})
    canvas = _resolve("canvas", pal)            # 대부분 white 별칭, 다크룩만 어두움
    dark = _lum(canvas) < 0.30
    ink = "#FFFFFF" if dark else _resolve("navy", pal)
    sub = "#C9CDD2" if dark else "#64748B"
    accent = _resolve("blue", pal)
    navy = _resolve("navy", pal)
    ramp = _chart_ramp(pal)
    fonts_blk = lk.get("fonts", {}) or {}
    font = fonts_blk.get("latin", "Inter")
    body_ea = fonts_blk.get("ea", "Pretendard")
    disp = fonts_blk.get("display", {}) or {}
    disp_ea = disp.get("ea")            # e.g. 송명; None when look has no display tier
    track = lk.get("track", "ppt")
    premium = bool(lk.get("premium"))
    return dict(slug=slug, canvas=canvas, dark=dark, ink=ink, sub=sub,
                accent=accent, navy=navy, ramp=ramp, font=font,
                body_ea=body_ea, disp_ea=disp_ea,
                track=track, premium=premium)


def card_html(v):
    bars = "".join(
        f'<span class="bar" style="background:{c};height:{h}%"></span>'
        for c, h in zip(v["ramp"], (62, 92, 44, 74)))
    swatches = "".join(
        f'<span class="sw" style="background:{c}" title="{lbl}"></span>'
        for lbl, c in (("accent", v["accent"]), ("accent2", v["ramp"][1]),
                       ("navy", v["navy"]), ("canvas", v["canvas"])))
    badges = (f'<span class="bg t-{v["track"]}">{v["track"].upper()}</span>'
              + (f'<span class="bg tone">{"다크" if v["dark"] else "라이트"}</span>')
              + (f'<span class="bg prem">PREMIUM</span>' if v["premium"] else ""))
    ff = html.escape(v["font"])
    disp_ea = v.get("disp_ea")
    # Korean glyphs in the headline fall back to the display face (송명) when the
    # look declares one; Latin glyphs always use the latin face. Body preview shows
    # the body ea face. Meta labels the cover/body split so picking is informed.
    ko_face = f"'{html.escape(disp_ea)}'," if disp_ea else ""
    title_ff = f"'{ff}',{ko_face}system-ui,'Pretendard',sans-serif"
    body_ff = f"'{html.escape(v['body_ea'])}','{ff}',system-ui,'Pretendard',sans-serif"
    font_label = (f"{ff} · 표지 {html.escape(disp_ea)} / 본문 {html.escape(v['body_ea'])}"
                  if disp_ea else ff)
    q_extra = f" {disp_ea.lower()} {v['body_ea'].lower()}" if disp_ea else ""
    return f'''<div class="card" data-track="{v['track']}" data-tone="{"dark" if v["dark"] else "light"}" data-q="{html.escape(v['slug'].lower())} {ff.lower()}{html.escape(q_extra)}">
  <div class="slide" style="background:{v['canvas']}">
    <div class="eyebrow" style="color:{v['accent']}">DESIGN · {v['track'].upper()}</div>
    <div class="title" style="color:{v['ink']};font-family:{title_ff}">Aa 디자인 제목<br>Sample Headline</div>
    <div class="accentbar" style="background:{v['accent']}"></div>
    <div class="sub" style="color:{v['sub']};font-family:{body_ff}">본문 미리보기 · body preview</div>
    <div class="bars">{bars}</div>
  </div>
  <div class="meta">
    <div class="name">{html.escape(v['slug'])}</div>
    <div class="font">{font_label}</div>
    <div class="row"><div class="sws">{swatches}</div><div class="badges">{badges}</div></div>
  </div>
</div>'''


def main():
    track_filter = None
    if "--track" in sys.argv:
        i = sys.argv.index("--track")
        if i + 1 < len(sys.argv):
            track_filter = sys.argv[i + 1]

    views = [look_view(s, lk) for s, lk in LOOKS.items()]
    views.sort(key=lambda v: (v["track"], not v["dark"], v["slug"]))
    fonts = sorted({v["font"] for v in views if v["font"]})
    # Display Korean faces (e.g. Song Myung) are loaded too so headline previews
    # render in the actual serif display face; unknown families Google ignores.
    ko_faces = sorted({v["disp_ea"] for v in views if v.get("disp_ea")})
    gf = "&".join("family=" + f.replace(" ", "+") for f in fonts + ko_faces)
    gf_link = (f'<link rel="preconnect" href="https://fonts.googleapis.com">'
               f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
               f'<link href="https://fonts.googleapis.com/css2?{gf}&display=swap" rel="stylesheet">')

    n_ppt = sum(1 for v in views if v["track"] == "ppt")
    n_web = sum(1 for v in views if v["track"] == "web")
    n_dark = sum(1 for v in views if v["dark"])
    cards = "\n".join(card_html(v) for v in views)
    preset = f"data-init-track=\"{track_filter}\"" if track_filter else ""

    doc = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ppt-lab-rebuild · 룩 갤러리 ({len(views)})</title>
{gf_link}
<style>
  :root{{--bd:#E2E8F0;--mut:#64748B}}
  *{{box-sizing:border-box}}
  body{{font-family:'Inter','Pretendard','Malgun Gothic',sans-serif;background:#F1F5F9;margin:0;color:#0F172A}}
  header{{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);
    border-bottom:1px solid var(--bd);padding:18px 28px}}
  h1{{font-size:18px;margin:0 0 4px}} .sub{{color:var(--mut);font-size:12.5px;margin-bottom:12px}}
  .ctrl{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
  .seg{{display:inline-flex;border:1px solid var(--bd);border-radius:8px;overflow:hidden}}
  .seg button{{border:0;background:#fff;padding:6px 12px;font-size:12.5px;cursor:pointer;color:#334155}}
  .seg button.on{{background:#0F172A;color:#fff}}
  input.search{{border:1px solid var(--bd);border-radius:8px;padding:7px 12px;font-size:13px;min-width:200px;flex:1}}
  .count{{color:var(--mut);font-size:12px;margin-left:auto}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px;padding:24px 28px}}
  .card{{background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden;
    box-shadow:0 1px 2px rgba(15,23,42,.04);transition:.12s}}
  .card:hover{{box-shadow:0 8px 24px rgba(15,23,42,.10);transform:translateY(-2px)}}
  .slide{{aspect-ratio:16/9;padding:18px 20px;position:relative;display:flex;flex-direction:column;gap:7px;overflow:hidden}}
  .eyebrow{{font-size:9px;font-weight:700;letter-spacing:.12em}}
  .title{{font-size:19px;font-weight:700;line-height:1.12;letter-spacing:-.01em}}
  .accentbar{{width:42px;height:4px;border-radius:2px;margin:2px 0}}
  .slide .sub{{font-size:9.5px;margin:0}}
  .bars{{display:flex;align-items:flex-end;gap:6px;height:30px;margin-top:auto}}
  .bar{{width:16px;border-radius:2px 2px 0 0;display:inline-block}}
  .meta{{padding:12px 14px 14px;border-top:1px solid #F1F5F9}}
  .name{{font-size:13px;font-weight:650;word-break:break-all}}
  .font{{font-size:11.5px;color:var(--mut);margin:2px 0 9px}}
  .row{{display:flex;align-items:center;justify-content:space-between;gap:8px}}
  .sws{{display:flex;gap:5px}}
  .sw{{width:15px;height:15px;border-radius:4px;border:1px solid rgba(15,23,42,.12)}}
  .badges{{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}}
  .bg{{font-size:9px;font-weight:700;padding:2px 6px;border-radius:5px;letter-spacing:.03em}}
  .bg.t-ppt{{background:#EFF6FF;color:#2563EB}} .bg.t-web{{background:#F0FDF4;color:#16A34A}}
  .bg.tone{{background:#F1F5F9;color:#475569}} .bg.prem{{background:#FEF3C7;color:#B45309}}
  .empty{{padding:60px;text-align:center;color:#94A3B8;grid-column:1/-1}}
</style></head><body {preset}>
<header>
  <h1>ppt-lab-rebuild · 룩 갤러리</h1>
  <div class="sub">design-tokens.json 에서 자동 생성 (render-look-gallery.py) · {len(views)} 룩 (PPT {n_ppt} · WEB {n_web} · 다크 {n_dark}) · 토큰 목업(실제 PPTX 렌더 아님, 색·폰트·톤 미리보기용)</div>
  <div class="ctrl">
    <span class="seg" id="seg-track">
      <button data-v="all" class="on">전체</button><button data-v="ppt">PPT</button><button data-v="web">WEB</button></span>
    <span class="seg" id="seg-tone">
      <button data-v="all" class="on">라이트+다크</button><button data-v="light">라이트</button><button data-v="dark">다크</button></span>
    <input class="search" id="q" placeholder="룩 이름·폰트 검색 (예: dark, editorial, Archivo)">
    <span class="count" id="count"></span>
  </div>
</header>
<div class="grid" id="grid">
{cards}
<div class="empty" id="empty" style="display:none">조건에 맞는 룩이 없습니다.</div>
</div>
<script>
const cards=[...document.querySelectorAll('.card')];
let fTrack='all',fTone='all',fQ='';
function seg(id,set){{document.querySelectorAll('#'+id+' button').forEach(b=>{{
  b.onclick=()=>{{document.querySelectorAll('#'+id+' button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');set(b.dataset.v);apply();}};}});}}
seg('seg-track',v=>fTrack=v); seg('seg-tone',v=>fTone=v);
document.getElementById('q').addEventListener('input',e=>{{fQ=e.target.value.trim().toLowerCase();apply();}});
function apply(){{let n=0;cards.forEach(c=>{{
  const ok=(fTrack==='all'||c.dataset.track===fTrack)
    &&(fTone==='all'||c.dataset.tone===fTone)
    &&(fQ===''||c.dataset.q.includes(fQ));
  c.style.display=ok?'':'none'; if(ok)n++;}});
  document.getElementById('empty').style.display=n?'none':'';
  document.getElementById('count').textContent=n+' 룩';}}
const initT=document.body.getAttribute('data-init-track');
if(initT){{document.querySelector('#seg-track button[data-v="'+initT+'"]')?.click();}}
apply();
</script></body></html>'''
    out = os.path.join(REF, "look-gallery.html")
    open(out, "w", encoding="utf-8").write(doc)
    print(f"[look-gallery] {len(views)} 룩 -> {out} ({len(doc)} bytes)")


if __name__ == "__main__":
    main()
