#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract-style.py — PPTX "스타일 프로파일" 측정기 (ppt-lab 흡수 1단계 · STYLE 축)

extract-pptx.py 는 좌표·역할(=Layout 축)을 뽑는다.
이 도구는 그와 직교하는 STYLE 축을 뽑는다. 두 종류의 신호를 측정한다:

  A. 선언된 기본값 (declared)   ← 추론 0, 권위적. 테마/마스터에서 그냥 읽음.
       - 테마 color scheme (dk1/lt1/dk2/lt2/accent1..6)
       - 테마 기본 폰트 (major/minor)
       - 배경 캐스케이드 (slide→layout→master) + fill 타입(solid/gradient/image)

  B. 창발적 반복 (emergent)      ← per-shape modal 집계. "반복되는 처리만" 스타일로 승격.
       - 도형 geometry (rect vs roundRect) + radius
       - fill 전략 (solid/gradient/image/none/styleRef)
       - 테두리(ln) 사용률 + modal 두께·색
       - 그림자(outerShdw) 사용률 + modal blur/dist/dir

python-pptx 고수준 API 는 그림자·radius·gradient·테마RGB 를 노출하지 않으므로
zipfile + lxml 로 OOXML 을 직접 파싱한다.

출력:
  - 화면: A/B 요약 + 9섹션 스키마 매핑(awesome-design-md 컨벤션 차용)
  - <pptx>_style.json: 기계가 읽을 스타일 프로파일

Usage:
  python3 extract-style.py deck.pptx
"""
import sys, os, json, argparse, zipfile, collections, statistics
from lxml import etree

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EMU_PER_PX = 9525
EMU_PER_PT = 12700
DEG = 60000  # dir 은 60000분의 1도

SYS = {"windowText": "000000", "window": "FFFFFF"}


def q(tag):
    pfx, local = tag.split(":")
    return "{%s}%s" % (NS[pfx], local)


# ---------------------------------------------------------------------------
# 색 해석 (srgbClr / sysClr / schemeClr)
# ---------------------------------------------------------------------------
def color_from_el(el, theme, clrmap, depth=0):
    """a:* 색 컨테이너의 첫 색 자식을 hex 로 해석. 수식어(lumMod 등)는 존재만 표시."""
    if el is None:
        return None
    for child in el:
        t = etree.QName(child).localname
        if t == "srgbClr":
            return "#" + child.get("val", "").upper()
        if t == "sysClr":
            return "#" + (child.get("lastClr") or SYS.get(child.get("val", ""), "000000")).upper()
        if t == "schemeClr" and depth < 4:
            name = child.get("val", "")
            # clrMap: tx1/bg1/tx2/bg2 → dk1/lt1/dk2/lt2
            mapped = clrmap.get(name, name)
            ref = theme.get(mapped) or theme.get(name)
            return ref
    return None


def parse_theme(z):
    """theme1.xml → {dk1,lt1,dk2,lt2,accent1..6,...}, fonts{major,minor}."""
    pal, fonts = {}, {}
    try:
        root = etree.fromstring(z.read("ppt/theme/theme1.xml"))
    except Exception:
        return pal, fonts
    scheme = root.find(".//" + q("a:clrScheme"))
    if scheme is not None:
        for c in scheme:
            name = etree.QName(c).localname
            # 색 자식 직접 해석 (schemeClr 재귀 없이 srgb/sys 만)
            for sub in c:
                st = etree.QName(sub).localname
                if st == "srgbClr":
                    pal[name] = "#" + sub.get("val", "").upper()
                elif st == "sysClr":
                    pal[name] = "#" + (sub.get("lastClr") or SYS.get(sub.get("val", ""), "000000")).upper()
    fs = root.find(".//" + q("a:fontScheme"))
    if fs is not None:
        for role, tag in (("major", "a:majorFont"), ("minor", "a:minorFont")):
            grp = fs.find(q(tag))
            if grp is not None:
                latin = grp.find(q("a:latin"))
                ea = grp.find(q("a:ea"))
                fonts[role] = {
                    "latin": latin.get("typeface") if latin is not None else None,
                    "ea": (ea.get("typeface") if ea is not None and ea.get("typeface") else None),
                }
    return pal, fonts


def parse_clrmap(z):
    """slideMaster 의 p:clrMap (tx1→dk1 등). 없으면 기본값."""
    default = {"bg1": "lt1", "tx1": "dk1", "bg2": "lt2", "tx2": "dk2"}
    try:
        root = etree.fromstring(z.read("ppt/slideMasters/slideMaster1.xml"))
        cm = root.find(q("p:clrMap"))
        if cm is not None:
            return {k: cm.get(k) for k in cm.keys()}
    except Exception:
        pass
    return default


# ---------------------------------------------------------------------------
# 배경 캐스케이드
# ---------------------------------------------------------------------------
def bg_of_xml(xml_bytes, theme, clrmap):
    """p:bg 가 있으면 fill 타입/색을 반환, 없으면 None."""
    try:
        root = etree.fromstring(xml_bytes)
    except Exception:
        return None
    bg = root.find(".//" + q("p:bg"))
    if bg is None:
        return None
    # solid
    sf = bg.find(".//" + q("a:solidFill"))
    if sf is not None:
        return {"fill": "solid", "color": color_from_el(sf, theme, clrmap)}
    gf = bg.find(".//" + q("a:gradFill"))
    if gf is not None:
        stops = []
        for gs in gf.findall(".//" + q("a:gs")):
            stops.append({"pos": round(int(gs.get("pos", "0")) / 1000, 1),
                          "color": color_from_el(gs, theme, clrmap)})
        ang = gf.find(".//" + q("a:lin"))
        return {"fill": "gradient", "stops": stops,
                "angle_deg": (round(int(ang.get("ang", "0")) / DEG) if ang is not None else None)}
    if bg.find(".//" + q("a:blipFill")) is not None:
        return {"fill": "image"}
    return {"fill": "other"}


def resolve_background(z, theme, clrmap, n_slides):
    """slide1 → layout → master 순으로 효과적 배경 결정 + slide override 수 카운트."""
    overrides = 0
    for i in range(1, n_slides + 1):
        try:
            if bg_of_xml(z.read("ppt/slides/slide%d.xml" % i), theme, clrmap):
                overrides += 1
        except Exception:
            pass
    # 효과적 배경: slide1 → layout1 → master1
    eff, src = None, None
    try:
        eff = bg_of_xml(z.read("ppt/slides/slide1.xml"), theme, clrmap)
        if eff: src = "slide"
    except Exception:
        pass
    if not eff:
        for path, name in (("ppt/slideLayouts/slideLayout1.xml", "layout"),
                           ("ppt/slideMasters/slideMaster1.xml", "master")):
            try:
                eff = bg_of_xml(z.read(path), theme, clrmap)
                if eff:
                    src = name
                    break
            except Exception:
                pass
    return {"source": src, **(eff or {"fill": None}), "slide_level_overrides": overrides}


# ---------------------------------------------------------------------------
# 창발적 per-shape 집계
# ---------------------------------------------------------------------------
def parse_shape_style(sp, theme, clrmap):
    """p:sp 하나의 spPr 에서 geometry/fill/line/shadow 신호 추출."""
    spPr = sp.find(q("p:spPr"))
    if spPr is None:
        return None
    out = {}
    # geometry + radius
    geom = spPr.find(q("a:prstGeom"))
    if geom is not None:
        prst = geom.get("prst")
        out["geom"] = prst
        if prst == "roundRect":
            gd = geom.find(".//" + q("a:gd"))
            out["adj"] = int(gd.get("fmla", "val 16667").split()[-1]) if gd is not None else 16667
    else:
        out["geom"] = "custom" if spPr.find(q("a:custGeom")) is not None else None
    # fill
    if spPr.find(q("a:solidFill")) is not None: out["fill"] = "solid"
    elif spPr.find(q("a:gradFill")) is not None: out["fill"] = "gradient"
    elif spPr.find(q("a:blipFill")) is not None: out["fill"] = "image"
    elif spPr.find(q("a:noFill")) is not None: out["fill"] = "none"
    else: out["fill"] = "styleRef"  # p:style/a:fillRef 상속
    # line
    ln = spPr.find(q("a:ln"))
    if ln is not None:
        if ln.find(q("a:noFill")) is not None:
            out["border"] = False
        else:
            out["border"] = True
            w = ln.get("w")
            out["border_w_pt"] = round(int(w) / EMU_PER_PT, 2) if w else None
            out["border_color"] = color_from_el(ln.find(q("a:solidFill")), theme, clrmap)
    else:
        out["border"] = None  # 미지정(상속)
    # shadow
    sh = spPr.find(".//" + q("a:outerShdw"))
    if sh is not None:
        out["shadow"] = {
            "blur_pt": round(int(sh.get("blurRad", "0")) / EMU_PER_PT, 1),
            "dist_pt": round(int(sh.get("dist", "0")) / EMU_PER_PT, 1),
            "dir_deg": round(int(sh.get("dir", "0")) / DEG),
        }
    return out


def aggregate(z, theme, clrmap, n_slides):
    geoms = collections.Counter()
    fills = collections.Counter()
    adj_vals, border_ws, shadow_blurs, shadow_dists, shadow_dirs = [], [], [], [], []
    border_colors = collections.Counter()
    n_shapes = n_border = n_shadow = 0
    for i in range(1, n_slides + 1):
        try:
            root = etree.fromstring(z.read("ppt/slides/slide%d.xml" % i))
        except Exception:
            continue
        for sp in root.iter(q("p:sp")):
            st = parse_shape_style(sp, theme, clrmap)
            if not st:
                continue
            n_shapes += 1
            if st.get("geom"): geoms[st["geom"]] += 1
            fills[st.get("fill", "?")] += 1
            if "adj" in st: adj_vals.append(st["adj"])
            if st.get("border") is True:
                n_border += 1
                if st.get("border_w_pt"): border_ws.append(st["border_w_pt"])
                if st.get("border_color"): border_colors[st["border_color"]] += 1
            if st.get("shadow"):
                n_shadow += 1
                shadow_blurs.append(st["shadow"]["blur_pt"])
                shadow_dists.append(st["shadow"]["dist_pt"])
                shadow_dirs.append(st["shadow"]["dir_deg"])

    def modal(lst):
        return collections.Counter(lst).most_common(1)[0][0] if lst else None

    rounded = geoms.get("roundRect", 0)
    rect_like = geoms.get("rect", 0) + rounded
    return {
        "shapes_scanned": n_shapes,
        "geometry": dict(geoms.most_common()),
        "rounded_pct": round(100 * rounded / rect_like) if rect_like else 0,
        "radius_modal_adj": modal(adj_vals),
        "radius_note": ("sharp(각진)" if rounded == 0 else
                        "adj~%s (min변 대비 %.1f%%)" % (modal(adj_vals), (modal(adj_vals) or 0) / 1000)),
        "fill_strategy_pct": {k: round(100 * v / n_shapes) for k, v in fills.items()} if n_shapes else {},
        "border": {
            "present_pct": round(100 * n_border / n_shapes) if n_shapes else 0,
            "modal_width_pt": modal(border_ws),
            "modal_color": border_colors.most_common(1)[0][0] if border_colors else None,
        },
        "shadow": {
            "present_pct": round(100 * n_shadow / n_shapes) if n_shapes else 0,
            "modal_blur_pt": modal(shadow_blurs),
            "modal_dist_pt": modal(shadow_dists),
            "modal_dir_deg": modal(shadow_dirs),
        },
    }


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    a = ap.parse_args()

    z = zipfile.ZipFile(a.pptx)
    n_slides = sum(1 for n in z.namelist()
                   if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    theme, fonts = parse_theme(z)
    clrmap = parse_clrmap(z)
    bg = resolve_background(z, theme, clrmap, n_slides)
    emergent = aggregate(z, theme, clrmap, n_slides)

    profile = {
        "source": os.path.basename(a.pptx),
        "slides_scanned": n_slides,
        "declared": {"theme_palette": theme, "fonts": fonts, "background": bg},
        "emergent": emergent,
        # awesome-design-md 9섹션 매핑 (pptx 에 해당하는 섹션만)
        "design_md_9section": {
            "color": {"scheme": theme, "background": bg.get("color") or bg.get("fill")},
            "typography": fonts,
            "spacing": "TODO: 형제 도형 gap 리듬 (v2)",
            "layout": "→ extract-pptx.py (Layout 축)",
            "components": {
                "card_corner": emergent["radius_note"],
                "card_border": "%d%% 도형에 테두리 (modal %s pt)" % (
                    emergent["border"]["present_pct"], emergent["border"]["modal_width_pt"]),
                "card_shadow": "%d%% 도형에 그림자 (blur %s / dist %s pt / %s°)" % (
                    emergent["shadow"]["present_pct"], emergent["shadow"]["modal_blur_pt"],
                    emergent["shadow"]["modal_dist_pt"], emergent["shadow"]["modal_dir_deg"]),
            },
            "motion": "N/A (정적 pptx)",
            "voice": "→ copy-guide (별도)",
            "brand": {"accents": [theme.get("accent%d" % i) for i in range(1, 7)]},
            "anti_patterns": {
                "uses_gradient_bg": bg.get("fill") == "gradient",
                "uses_rounded": emergent["rounded_pct"] > 0,
            },
        },
    }

    out = os.path.splitext(a.pptx)[0] + "_style.json"
    json.dump(profile, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ── 화면 요약 ──
    print("\n══ STYLE PROFILE: %s (%d 슬라이드) ══" % (profile["source"], n_slides))
    print("\n[A. 선언된 기본값]")
    print("  테마 팔레트:")
    for k in ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6"):
        if k in theme:
            print("     %-8s %s" % (k, theme[k]))
    print("  기본 폰트: major=%s / minor=%s" % (
        (fonts.get("major") or {}).get("latin"), (fonts.get("minor") or {}).get("latin")))
    print("  배경: [%s] fill=%s color=%s (slide override %d장)" % (
        bg.get("source"), bg.get("fill"), bg.get("color"), bg.get("slide_level_overrides")))
    if bg.get("fill") == "gradient":
        print("        stops=%s angle=%s°" % (bg.get("stops"), bg.get("angle_deg")))

    print("\n[B. 창발적 반복] (%d 도형)" % emergent["shapes_scanned"])
    print("  geometry: %s" % emergent["geometry"])
    print("  모서리: %s" % emergent["radius_note"])
    print("  fill 전략(%%): %s" % emergent["fill_strategy_pct"])
    print("  테두리: %d%% 도형 / modal %s pt / %s" % (
        emergent["border"]["present_pct"], emergent["border"]["modal_width_pt"],
        emergent["border"]["modal_color"]))
    print("  그림자: %d%% 도형 / blur %s · dist %s pt · %s°" % (
        emergent["shadow"]["present_pct"], emergent["shadow"]["modal_blur_pt"],
        emergent["shadow"]["modal_dist_pt"], emergent["shadow"]["modal_dir_deg"]))
    print("\n✅ 저장: %s" % out)


if __name__ == "__main__":
    main()
