#!/usr/bin/env python3
"""gen-texture.py — 절차적 슬라이드 배경/텍스처 생성기 (모델 없음, 결정론적).

AI 이미지 생성(gen-image.py, 별도 브랜치)과 달리 **코드로 그린다** — 키·비용·네트워크 0,
같은 입력 → 항상 같은 출력(재현). 덱이 실제로 자주 쓰는 추상 배경/질감 전용:
그라디언트·메시·글로우·도트·그레인. (사람·제품 같은 실사는 이걸로 안 됨 → AI 경로)

룩 팔레트 자동 채색: `--look <slug>` 이면 design-tokens.json 의 그 룩 canvas/accents 로
색을 끌어와 덱과 결을 맞춘다. 또는 `--colors "#a,#b,..."` / `--canvas` / `--accent` 직접 지정.

출력: PNG 1장을 <slides-dir>/assets/ (또는 --out)에 저장 + 경로 stdout 출력
      → spec 의 `background`/`media`/`image` 의 `src` 에 그대로 꽂기.

예:
  python3 gen-texture.py --kind mesh  --look ppt-glassmorphism      --slides-dir /mnt/c/dev/decks/d --name bg
  python3 gen-texture.py --kind glow  --look ppt-dark-luxury-keynote --name hero
  python3 gen-texture.py --kind linear --colors "#0C1A17,#123" --angle 60 --out /tmp/grad.png
  python3 gen-texture.py --kind grain --canvas "#F2F0EB" --seed 7
"""
import argparse
import json
import math
import pathlib
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TOKENS = pathlib.Path(__file__).resolve().parent.parent / "design-tokens.json"
KINDS = ("mesh", "linear", "glow", "dots", "grain", "solid")


# ---------- 색 유틸 ----------
def hex_rgb(h):
    h = str(h).lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def resolve_palette(look_slug):
    """룩 슬러그 → (canvas_hex, [accent_hex...]). role 토큰은 같은 팔레트 내에서 해석."""
    data = json.loads(TOKENS.read_text(encoding="utf-8"))
    look = data.get("looks", {}).get(look_slug)
    if not look:
        sys.exit(f"[gen-texture] 룩 '{look_slug}' 없음 (design-tokens.json)")
    pal = look.get("palette", {})

    def res(tok):
        if isinstance(tok, str) and tok.startswith("#"):
            return tok
        return pal.get(tok, tok if str(tok).startswith("#") else pal.get("blue", "#888888"))

    canvas = pal.get("canvas") or "#FFFFFF"
    roles = pal.get("accents") or ["blue"]
    accents = [res(r) for r in roles]
    # 변주용 틴트도 보강(메시·그라디언트에서 색 수 부족하면 사용)
    for extra in ("blue-2", "blue-light", "orange"):
        if pal.get(extra) and pal[extra] not in accents:
            accents.append(pal[extra])
    return canvas, accents


def pick_colors(args, n_min=2):
    """우선순위: --colors > --look > (--canvas/--accent) > 폴백."""
    if args.colors:
        cols = [hex_rgb(c) for c in args.colors.split(",") if c.strip()]
    elif args.look:
        canvas, accents = resolve_palette(args.look)
        cols = [hex_rgb(c) for c in ([canvas] + accents)]
    elif args.canvas or args.accent:
        cols = [hex_rgb(args.canvas or "#0C1A17"), hex_rgb(args.accent or "#3FA9FF")]
    else:  # 폴백(글래스 메시)
        cols = [hex_rgb(c) for c in ("#7B5BFF", "#3FA9FF", "#FF6FB5", "#48E1C8")]
    while len(cols) < n_min:
        cols.append(cols[-1])
    return cols


def base_canvas(args, default="#0C1A17"):
    if args.canvas:
        return hex_rgb(args.canvas)
    if args.look:
        canvas, _ = resolve_palette(args.look)
        return hex_rgb(canvas)
    if args.colors:
        return hex_rgb(args.colors.split(",")[0])
    return hex_rgb(default)


def accents_only(args):
    if args.colors:
        c = [hex_rgb(x) for x in args.colors.split(",") if x.strip()]
        return c[1:] or c
    if args.look:
        _, accents = resolve_palette(args.look)
        return [hex_rgb(a) for a in accents]
    if args.accent:
        return [hex_rgb(args.accent)]
    return [hex_rgb("#3FA9FF"), hex_rgb("#7B5BFF")]


# ---------- 생성기 ----------
def gen_mesh(w, h, cols):
    """4코너 바이리니어 메시 그라디언트(글래스 배경). 색 4개로 코너 채움."""
    while len(cols) < 4:
        cols.append(cols[len(cols) % len(cols)])
    tl, tr, bl, br = [np.array(c, float) for c in cols[:4]]
    x = np.linspace(0, 1, w)[None, :, None]
    y = np.linspace(0, 1, h)[:, None, None]
    top = tl * (1 - x) + tr * x
    bot = bl * (1 - x) + br * x
    img = top * (1 - y) + bot * y
    return np.clip(img, 0, 255).astype("uint8")


def gen_linear(w, h, cols, angle):
    """각도 다중스톱 선형 그라디언트."""
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    xx, yy = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    t = xx * dx + yy * dy
    rng = (t.max() - t.min()) or 1.0
    t = (t - t.min()) / rng
    cols = np.array(cols, float)
    pos = np.linspace(0, 1, len(cols))
    out = np.empty((h, w, 3))
    for c in range(3):
        out[..., c] = np.interp(t, pos, cols[:, c])
    return np.clip(out, 0, 255).astype("uint8")


def gen_glow(w, h, base, orbs, intensity):
    """다크 베이스 + 가산(additive) 라디얼 글로우 오브 — 발광 미감."""
    img = np.zeros((h, w, 3), float) + np.array(base, float)
    yy, xx = np.mgrid[0:h, 0:w]
    spots = [(0.78, 0.18), (0.15, 0.85), (0.5, 0.5)]   # 결정론적 배치
    for i, color in enumerate(orbs):
        cx, cy = spots[i % len(spots)]
        cx *= w; cy *= h
        radius = 0.55 * min(w, h)
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        fall = np.clip(1 - dist / radius, 0, 1) ** 2.2
        img += np.array(color, float)[None, None, :] * fall[..., None] * intensity
    return np.clip(img, 0, 255).astype("uint8")


def gen_dots(w, h, base, dot, gap, dot_alpha):
    """베이스 위 미세 도트 그리드(테크/블루프린트). 알파로 은은하게."""
    im = Image.new("RGB", (w, h), base)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = max(1, w // 960)        # 점 반경 ~2px@1920
    g = gap or max(16, w // 60)
    col = tuple(dot) + (dot_alpha,)
    for yy in range(g, h, g):
        for xx in range(g, w, g):
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=col)
    return np.array(Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB"))


def gen_grain(w, h, base, accent, seed, sigma):
    """베이스(또는 베이스→액센트 미세 수직 그라디언트) + 필름 그레인 노이즈."""
    rng = np.random.default_rng(seed)
    b = np.array(base, float)
    a = np.array(accent, float)
    yv = np.linspace(0, 0.18, h)[:, None, None]      # 아주 옅은 톤 시프트
    img = b[None, None, :] * (1 - yv) + a[None, None, :] * yv
    img = np.repeat(img, w, axis=1) if img.shape[1] == 1 else img
    noise = rng.normal(0, sigma, (h, w, 1))
    return np.clip(img + noise, 0, 255).astype("uint8")


# ---------- 저장/CLI ----------
def resolve_out(args):
    if args.out:
        p = pathlib.Path(args.out).with_suffix(".png")
    else:
        base = pathlib.Path(args.slides_dir) if args.slides_dir else pathlib.Path.cwd()
        name = args.name or f"{args.kind}-bg"
        p = base / "assets" / f"{name}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def main():
    ap = argparse.ArgumentParser(description="절차적 슬라이드 텍스처 생성기(모델 없음)")
    ap.add_argument("--kind", required=True, choices=KINDS)
    ap.add_argument("--look", help="design-tokens 룩 슬러그 → 팔레트 자동 채색")
    ap.add_argument("--colors", help='쉼표 hex 목록 "#a,#b,#c" (룩보다 우선)')
    ap.add_argument("--canvas", help="베이스 색 hex(glow/dots/grain)")
    ap.add_argument("--accent", help="액센트 색 hex")
    ap.add_argument("--size", default="1920x1080", help="WxH (기본 1920x1080)")
    ap.add_argument("--angle", type=float, default=45, help="linear 각도(도)")
    ap.add_argument("--seed", type=int, default=7, help="grain 시드(결정론)")
    ap.add_argument("--intensity", type=float, default=0.9, help="glow 세기")
    ap.add_argument("--blur", type=float, default=0, help="마무리 가우시안 블러 px")
    ap.add_argument("--out")
    ap.add_argument("--slides-dir")
    ap.add_argument("--name")
    args = ap.parse_args()

    w, h = (int(v) for v in args.size.lower().split("x"))

    if args.kind == "mesh":
        arr = gen_mesh(w, h, pick_colors(args, 4))
    elif args.kind == "linear":
        arr = gen_linear(w, h, pick_colors(args, 2), args.angle)
    elif args.kind == "glow":
        arr = gen_glow(w, h, base_canvas(args), accents_only(args), args.intensity)
    elif args.kind == "dots":
        acc = accents_only(args)[0]
        arr = gen_dots(w, h, base_canvas(args, "#0C1A17"), acc, gap=0, dot_alpha=40)
    elif args.kind == "grain":
        acc = accents_only(args)[0]
        arr = gen_grain(w, h, base_canvas(args, "#F2F0EB"), acc, args.seed, sigma=7.0)
    elif args.kind == "solid":
        arr = np.zeros((h, w, 3), "uint8") + np.array(base_canvas(args), "uint8")

    img = Image.fromarray(arr, "RGB")
    if args.blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(args.blur))
    out = resolve_out(args)
    img.save(out)
    print(str(out))


if __name__ == "__main__":
    main()
