#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract-look.py — 생짜 .pptx 자동 흡수기 (ppt-lab 흡수 · LOOK 번들 작성)

임의의 `.pptx`를 던지면 `design-tokens.json`의 `looks{<slug>}` 한 엔트리를
**결정론적으로 자동 작성·append** 한다. design-pick 토큰이 있을 때만 흡수하던
absorb-design-pick-looks.py 를 "토큰 없는 생짜 덱"으로 일반화한 도구.

4단계 (전부 결정론, 토큰 거의 안 듦):
  1. 폰트 + 카드  : extract-style.py 측정 로직 재사용
                    → fonts{latin,ea} (한글 폰트는 latin 슬롯에서 제외)
                    → components.card{radius,fill,border,shadow}
  2. 팔레트(신규) : 슬라이드 XML 의 solidFill 색 수집 → 배경/무채색 제외 →
                    빈도+채도 가중으로 **지배 강조색** 추출 →
                    absorb-design-pick-looks.py 의 ramp()/mixc()/navy/accents 로 램프 구성.
                    무채색 덱이면 accent = 잉크색(파랑 폴백 금지).
  3. 조립        : slug / _from / attribution / track 추정 → looks 엔트리 →
                    "typography" 키 앞에 idempotent 텍스트 삽입(동일 slug 면 교체).
  4. 검증        : build-template.py --look <slug> 데모 빌드로 소비 가능 확인.

Usage:
  python3 tools/extract-look.py <input.pptx> [--slug <slug>] \
      [--source "..."] [--license "..."] [--track ppt|web] [--caption "..."] \
      [--no-build]

함정(HANDOFF §3) 반영:
  - shadow color 는 hex 직박음, alpha 는 투명도(=100-alpha, 0=불투명).
    하드섀도=blur0/alpha0, 소프트≈alpha82.
  - card.fill 은 밝은 surface 면 hex, 아니면 'slate-50'.
  - 무채색 덱 → accent=잉크색, 파랑 폴백 금지.
  - 한글 폰트가 latin 슬롯으로 잡히지 않게 Hangul 정규식 제외.
"""
import sys, os, re, json, argparse, zipfile, collections, colorsys, subprocess

# extract-style.py 와 같은 디렉토리에 있으므로 측정 로직을 직접 import 해 재사용한다.
# (DRY — 테마/폰트/배경/도형-스타일 파싱은 extract-style.py 가 권위 소스.)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import importlib.util as _ilu

def _load_module(fname, modname):
    spec = _ilu.spec_from_file_location(modname, os.path.join(_HERE, fname))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# 하이픈 파일명이라 import 문으로는 못 부른다 → spec 로더로 로드.
_es = _load_module("extract-style.py", "extract_style")
parse_theme = _es.parse_theme
parse_clrmap = _es.parse_clrmap
resolve_background = _es.resolve_background
aggregate = _es.aggregate
q = _es.q
NS = _es.NS

TOKENS_PATH = os.path.join(os.path.dirname(_HERE), "design-tokens.json")

# ---------------------------------------------------------------------------
# 색 헬퍼 — absorb-design-pick-looks.py 에서 그대로 차용 (램프/믹스/루마).
#   출처: references/tools/absorb-design-pick-looks.py
# ---------------------------------------------------------------------------
HEX = re.compile(r'^#?[0-9A-Fa-f]{6}$')
def is_hex(s): return isinstance(s, str) and bool(HEX.match(s.strip()))
def norm(h): return '#' + h.strip().lstrip('#').upper()
def rgb(h):
    h = h.strip().lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def luma(h):
    r, g, b = rgb(h); return (0.299 * r + 0.587 * g + 0.114 * b) / 255
def mixc(h, t, f):  # mix h toward t by f
    a, b = rgb(h), rgb(t); g = lambda i: round(a[i] + (b[i] - a[i]) * f)
    return f"#{g(0):02X}{g(1):02X}{g(2):02X}"
def ramp(p):
    return {"blue": norm(p), "blue-2": mixc(p, '#FFFFFF', 0.22),
            "blue-light": mixc(p, '#FFFFFF', 0.55),
            "blue-pale": mixc(p, '#FFFFFF', 0.80),
            "blue-faint": mixc(p, '#FFFFFF', 0.93)}

# 한글 폰트 키워드 — latin 슬롯에서 배제 (absorb-design-pick-looks.py 의 KOR 차용).
KOR = ('Pretendard', 'Malgun', '맑은', 'Noto Sans KR', 'Noto Serif KR', 'Gothic',
       'Nanum', 'Gowun', 'Han Sans', 'Apple SD', 'Spoqa', 'Batang', 'Gulim',
       'Dotum', 'Gungsuh', 'Droid Sans Fallback')
def is_latin(f):
    return (bool(f) and not any(k in f for k in KOR)
            and not any(k in f for k in ('KR', 'Kr'))
            and not re.search(r'[가-힣]', f))
def is_ea(f):
    return bool(f) and (any(k in f for k in ('Pretendard', 'Noto Sans KR', 'Noto Serif KR',
                                             'Gowun', 'Nanum', 'Spoqa', 'Malgun', '맑은'))
                        or bool(re.search(r'[가-힣]', f)))


# ---------------------------------------------------------------------------
# STEP 1 — 폰트 (테마 + run 실측)
# ---------------------------------------------------------------------------
def collect_run_fonts(z, n_slides):
    """슬라이드 run 의 a:latin / a:ea typeface 를 빈도 집계.
    테마 폰트가 'Droid Sans Fallback' 같은 렌더러 폴백일 때 실제 본문 폰트를 잡는다."""
    latin_c, ea_c = collections.Counter(), collections.Counter()
    for i in range(1, n_slides + 1):
        try:
            from lxml import etree
            root = etree.fromstring(z.read("ppt/slides/slide%d.xml" % i))
        except Exception:
            continue
        for rpr in root.iter(q("a:rPr")):
            for tag, ctr in (("a:latin", latin_c), ("a:ea", ea_c)):
                el = rpr.find(q(tag))
                if el is not None and el.get("typeface"):
                    ctr[el.get("typeface")] += 1
    return latin_c, ea_c


def pick_fonts(theme_fonts, latin_c, ea_c):
    """latin/ea 폰트 결정. 우선순위: run 실측(빈도순) → 테마 → 디폴트.
    한글 폰트는 latin 슬롯에서 제외, ea 슬롯은 한글 가능 폰트로 폴백."""
    # 후보 풀: run 실측(빈도 내림차순) + 테마 major/minor
    run_latin = [f for f, _ in latin_c.most_common()]
    run_ea = [f for f, _ in ea_c.most_common()]
    theme_latin = [(theme_fonts.get(r) or {}).get("latin") for r in ("major", "minor")]
    theme_ea = [(theme_fonts.get(r) or {}).get("ea") for r in ("major", "minor")]

    latin_pool = run_latin + [f for f in theme_latin if f]
    ea_pool = run_ea + [f for f in theme_ea if f] + run_latin

    latin = next((f for f in latin_pool if is_latin(f)), None) or "Inter"
    ea = next((f for f in ea_pool if is_ea(f)), None) or "Pretendard"
    return latin, ea


# ---------------------------------------------------------------------------
# STEP 1 — 카드(component) : extract-style.py 의 emergent 집계 → card 프리셋
# ---------------------------------------------------------------------------
def build_card(emergent):
    """창발적 집계(geometry/border/shadow modal)를 looks.components.card 로 변환.
    함정 반영: shadow color hex 직박음 / alpha=투명도(0=불투명) / fill 밝으면 hex."""
    notes = []
    # radius — roundRect modal adj 를 px 로 근사. adj 는 min변 대비 1/1000 비율.
    rad = 0
    if emergent.get("rounded_pct", 0) > 0 and emergent.get("radius_modal_adj"):
        # adj(예: 16667) → 대략 px. 카드 폭 ~320px·adj/100000 환산을 보수적으로.
        rad = max(0, round(emergent["radius_modal_adj"] / 1000))
        if rad > 24:
            rad = 24  # 카드 모서리 상한(과한 알약형 방지)

    # border
    bp = emergent.get("border", {})
    border = None
    if bp.get("present_pct", 0) >= 35:  # 1/3 이상 도형이 테두리 → 스타일 신호로 승격
        w = bp.get("modal_width_pt") or 0.75
        col = bp.get("modal_color")
        border = {"width_pt": round(float(w), 2),
                  "color": norm(col) if is_hex(col) else "slate-300"}
    else:
        notes.append("border-sparse")

    # shadow
    shp = emergent.get("shadow", {})
    shadow = None
    if shp.get("present_pct", 0) >= 25:
        blur = shp.get("modal_blur_pt") or 0
        dist = shp.get("modal_dist_pt") or 4
        d = shp.get("modal_dir_deg")
        hard = (blur == 0)
        shadow = {"blur_pt": round(float(blur), 1),
                  "dist_pt": round(float(dist), 1),
                  "dir_deg": int(d) if d is not None else (135 if hard else 90),
                  "color": "#1D1B20",          # 함정: hex 직박음
                  "alpha": 0 if hard else 82}   # 함정: 투명도(0=불투명), 소프트≈82
    return rad, border, shadow, notes


def pick_fill(bg, surface_candidates):
    """카드 fill 결정. 밝은 surface 면 그 hex, 아니면 토큰 'slate-50'."""
    for s in surface_candidates:
        if is_hex(s) and luma(s) > 0.85:
            return norm(s)
    return "slate-50"


# ---------------------------------------------------------------------------
# STEP 2 — 팔레트 : solidFill 색 수집 → 지배 강조색 추출 (신규 부분)
# ---------------------------------------------------------------------------
def collect_solid_colors(z, n_slides):
    """슬라이드 도형의 a:solidFill(srgbClr) 색을 빈도 집계.
    배경(p:bg) 안의 fill 은 슬라이드 도형이 아니므로 자연히 비중이 낮다."""
    from lxml import etree
    cnt = collections.Counter()
    for i in range(1, n_slides + 1):
        try:
            root = etree.fromstring(z.read("ppt/slides/slide%d.xml" % i))
        except Exception:
            continue
        for sf in root.iter(q("a:solidFill")):
            sc = sf.find(q("a:srgbClr"))
            if sc is not None and sc.get("val"):
                cnt["#" + sc.get("val").upper()] += 1
    return cnt


def _hsv(h):
    r, g, b = rgb(h); return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def is_achromatic(h):
    """배경/무채색(흰·검·회) 판정. 채도 매우 낮거나, 거의 흰/검이면 제외 대상."""
    H, S, V = _hsv(h)
    return S < 0.15 or V > 0.95 or V < 0.10


def _brightness_window(V):
    """강조색은 너무 어둡지도(=navy) 밝지도(=pastel) 않은 중간 명도가 이상적.
    V∈[0.45,0.85] 에서 1.0, 그 밖은 부드럽게 감쇠. 매우 어두운 색은 navy 후보로."""
    if V < 0.20:
        return 0.15          # 거의 navy/ink — 강조색으로는 비선호
    if V < 0.45:
        return 0.45 + (V - 0.20) * (0.55 / 0.25)  # 0.45→1.0 선형
    if V <= 0.85:
        return 1.0
    return max(0.2, 1.0 - (V - 0.85) * 4)          # 너무 밝으면 감쇠


def pick_dominant_accent(color_cnt):
    """빈도+채도+명도창 가중으로 지배 강조색 선택.
    반환: (accent_hex 또는 None, chromatic_여부, navy_candidate 또는 None)
    무채색뿐이면 accent=None → 호출부에서 잉크색 폴백."""
    scored = []
    navy_cands = []
    for h, freq in color_cnt.items():
        H, S, V = _hsv(h)
        if S >= 0.30 and V < 0.45:
            navy_cands.append((freq * S, h))  # 짙은 채색 → navy 후보
        if is_achromatic(h):
            continue
        score = freq * S * _brightness_window(V)
        if score > 0:
            scored.append((score, freq, h))
    if not scored:
        return None, False, (max(navy_cands)[1] if navy_cands else None)
    scored.sort(reverse=True)
    accent = scored[0][2]
    navy_candidate = max(navy_cands)[1] if navy_cands else None
    # 강조색을 제외한 두 번째 채색(있으면 보조 accent)
    secondary = next((h for _, _, h in scored[1:]
                      if abs(_hsv(h)[0] - _hsv(accent)[0]) > 0.08), None)
    return accent, secondary, navy_candidate


def build_palette(color_cnt, text_ink):
    """지배 강조색 + 보조색 + navy 로 looks.palette 구성.
    무채색 덱이면 accent=잉크색(파랑 폴백 금지)."""
    notes = []
    accent, secondary, navy_candidate = pick_dominant_accent(color_cnt)

    if accent is None:
        # 무채색/모노 덱 → 잉크색을 강조색으로 (절대 파랑 폴백 안 함).
        ink = norm(text_ink) if (text_ink and luma(text_ink) < 0.45) else "#1A1A1A"
        accent = ink
        secondary = None
        notes.append("accent=ink(mono, no-blue-fallback)")

    acc0 = norm(accent)
    acc1 = norm(secondary) if secondary else acc0

    # navy: 짙은 채색(브랜드 다크)을 최우선 — 순수 검정 잉크보다 정체성이 강하다.
    #       없으면 짙은 잉크, 그것도 없으면 accent 를 어둡게 믹스.
    if navy_candidate and luma(navy_candidate) < 0.45:
        navy = norm(navy_candidate)
    elif text_ink and 0.02 < luma(text_ink) < 0.35:
        navy = norm(text_ink)
    else:
        navy = mixc(acc0, "#000000", 0.72)

    pal = ramp(acc0)
    pal["navy"] = navy
    pal["orange"] = acc1
    accents = ["blue", "orange"] if secondary else ["blue"]
    pal["accents"] = accents
    return pal, acc0, notes


# ---------------------------------------------------------------------------
# STEP 3 — 조립 + idempotent 삽입
# ---------------------------------------------------------------------------
def slugify(name):
    s = os.path.splitext(os.path.basename(name))[0].lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or "extracted-look"


def infer_track(slide_w_emu, slide_h_emu):
    """16:9(또는 가로 와이드)면 ppt, 세로/긴 비율이면 web 추정. 기본 ppt."""
    if not slide_w_emu or not slide_h_emu:
        return "ppt"
    ratio = slide_w_emu / slide_h_emu
    return "web" if ratio < 1.0 else "ppt"


def read_slide_size(z):
    try:
        from lxml import etree
        root = etree.fromstring(z.read("ppt/presentation.xml"))
        sz = root.find(q("p:sldSz"))
        if sz is not None:
            return int(sz.get("cx", "0")), int(sz.get("cy", "0"))
    except Exception:
        pass
    return None, None


def insert_look(slug, look_entry):
    """design-tokens.json 의 looks 객체에 idempotent 삽입.
    동일 slug 존재 시 깔끔히 교체(중복 금지). 텍스트 삽입은 "typography" 앞."""
    text = open(TOKENS_PATH, encoding="utf-8").read()
    data = json.loads(text)
    existed = slug in data.get("looks", {})

    if existed:
        # 기존 엔트리 교체: 파싱한 dict 를 갱신 후 looks 블록 전체를 재직렬화 삽입.
        data["looks"][slug] = look_entry[slug]
        new_looks = data["looks"]
    else:
        new_looks = dict(data.get("looks", {}))
        new_looks[slug] = look_entry[slug]

    block = json.dumps(new_looks, ensure_ascii=False, indent=2)
    block = '\n'.join(('  ' + ln if ln else ln) for ln in block.split('\n'))  # indent 2

    # 기존 "looks": { ... } 블록을 통째로 치환(있으면), 없으면 "typography" 앞에 삽입.
    m = re.search(r'\n  "looks":\s*\{', text)
    if m:
        # 매칭 시작부터 균형 잡힌 닫는 중괄호까지 범위 찾기
        start = m.start() + 1  # 줄바꿈 제외, "  \"looks\"" 부터
        brace_open = text.index('{', m.start())
        depth = 0
        end = None
        for idx in range(brace_open, len(text)):
            ch = text[idx]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        # 닫는 } 뒤에 쉼표가 있으면 포함
        tail = end
        if tail < len(text) and text[tail] == ',':
            tail += 1
        new_text = text[:start] + f'  "looks": {block},' + text[tail:]
    else:
        ins = f'  "looks": {block},\n'
        anchor = re.search(r'\n  "typography":', text)
        new_text = text[:anchor.start() + 1] + ins + text[anchor.start() + 1:]

    open(TOKENS_PATH, "w", encoding="utf-8").write(new_text)
    json.load(open(TOKENS_PATH, encoding="utf-8"))  # validate parse
    return existed


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="생짜 pptx → looks{slug} 자동 흡수")
    ap.add_argument("pptx", help="입력 .pptx")
    ap.add_argument("--slug", default=None, help="룩 슬러그(생략 시 파일명에서 유도)")
    ap.add_argument("--source", default=None, help="출처 표기(attribution.source)")
    ap.add_argument("--license", default=None, help="라이선스(attribution.license)")
    ap.add_argument("--required", action="store_true",
                    help="귀속 표기 필수 여부(기본 false)")
    ap.add_argument("--track", default=None, choices=["ppt", "web"],
                    help="트랙(생략 시 슬라이드 비율로 추정)")
    ap.add_argument("--caption", default=None, help="attribution.caption")
    ap.add_argument("--no-build", action="store_true",
                    help="STEP4 데모 빌드 검증 건너뜀")
    args = ap.parse_args()

    if not os.path.isfile(args.pptx):
        sys.exit(f"[extract-look] 파일 없음: {args.pptx}")

    z = zipfile.ZipFile(args.pptx)
    n_slides = sum(1 for n in z.namelist()
                   if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    if n_slides == 0:
        sys.exit("[extract-look] 슬라이드가 없는 pptx")

    theme, theme_fonts = parse_theme(z)
    clrmap = parse_clrmap(z)
    bg = resolve_background(z, theme, clrmap, n_slides)
    emergent = aggregate(z, theme, clrmap, n_slides)

    # ── STEP 1: 폰트 ──
    latin_c, ea_c = collect_run_fonts(z, n_slides)
    latin, ea = pick_fonts(theme_fonts, latin_c, ea_c)

    # ── STEP 1: 카드 ──
    rad, border, shadow, card_notes = build_card(emergent)

    # 밝은 surface 후보: 배경색 + 테마 lt1
    surface_cands = [bg.get("color"), theme.get("lt1")]
    fill = pick_fill(bg, surface_cands)

    # ── STEP 2: 팔레트 ──
    color_cnt = collect_solid_colors(z, n_slides)
    text_ink = theme.get("dk1") or "#1A1A1A"
    palette, acc0, pal_notes = build_palette(color_cnt, text_ink)

    # ── STEP 3: 조립 ──
    slug = args.slug or slugify(args.pptx)
    cx, cy = read_slide_size(z)
    track = args.track or infer_track(cx, cy)
    source_label = (f"raw pptx '{os.path.basename(args.pptx)}' "
                    f"({track}) — extract-look.py 결정론 측정")

    look_entry = {
        slug: {
            "_from": source_label,
            "attribution": {
                "source": args.source or "extracted from raw .pptx (extract-look.py)",
                "license": args.license or "unknown (raw deck — verify before redistribution)",
                "required": bool(args.required),
                "caption": args.caption or f"look auto-extracted from {os.path.basename(args.pptx)}",
            },
            "track": track,
            "premium": False,
            "fonts": {"latin": latin, "ea": ea},
            "components": {"card": {"radius": rad, "fill": fill,
                                    "border": border, "shadow": shadow}},
            "palette": palette,
        }
    }

    existed = insert_look(slug, look_entry)

    # ── 요약 출력 ──
    print("\n══ EXTRACT-LOOK: %s (%d 슬라이드, track=%s) ══" %
          (os.path.basename(args.pptx), n_slides, track))
    print("  slug      : %s%s" % (slug, "  (기존 교체)" if existed else "  (신규)"))
    print("  fonts     : latin=%s / ea=%s" % (latin, ea))
    print("  card      : radius=%s fill=%s" % (rad, fill))
    print("              border=%s" % (border,))
    print("              shadow=%s" % (shadow,))
    print("  accent    : %s  (dominant)" % acc0)
    print("  palette   : navy=%s orange=%s accents=%s" %
          (palette["navy"], palette["orange"], palette["accents"]))
    allnotes = card_notes + pal_notes
    if allnotes:
        print("  notes     : %s" % ", ".join(allnotes))
    print("  appended  : %s  (looks 'typography' 앞)" % TOKENS_PATH)

    # ── STEP 4: 데모 빌드 검증 ──
    if not args.no_build:
        out = "/tmp/extract-look-test.pptx"
        cmd = ["python3", os.path.join(_HERE, "build-template.py"), out, "--look", slug]
        print("\n[verify] %s" % " ".join(cmd))
        r = subprocess.run(cmd, cwd=os.path.dirname(_HERE),
                           capture_output=True, text=True)
        if r.returncode == 0:
            print(r.stdout.strip())
            print("✅ 데모 빌드 성공 — looks 엔트리 소비 가능")
        else:
            print(r.stdout.strip())
            print(r.stderr.strip())
            print("❌ 데모 빌드 실패 — 엔트리 점검 필요")
            sys.exit(1)


if __name__ == "__main__":
    main()
