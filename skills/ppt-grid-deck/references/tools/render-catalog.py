#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render-catalog.py — layouts.json + design-tokens.json → catalog.html (자동 생성)

HTML 카탈로그를 손으로 안 고친다. layouts.json(진실)에서 매번 다시 찍어낸다 → drift 0.
각 변종의 슬롯을 240x135 와이어프레임 카드로 렌더.

Usage:
  python3 render-catalog.py        # references/catalog.html 갱신
"""
import json, os

REF = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOK = json.load(open(os.path.join(REF, "design-tokens.json"), encoding="utf-8"))
LAY = json.load(open(os.path.join(REF, "layouts.json"), encoding="utf-8"))

SCALE = 240.0 / 1920.0  # 1920px → 240 와이어프레임
VB_W, VB_H = 240, 135
BRAND = TOK["colors"].get("brand", "#2563EB")
INK = TOK["colors"].get("ink", "#0F172A")
LINE = TOK["colors"].get("line", "#E2E8F0")


def slot_rects(slots):
    out = []
    for name, box in slots.items():
        x, y, w, h = [v * SCALE for v in box]
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                   f'rx="2" fill="#EEF2FF" stroke="{BRAND}" stroke-width="0.8"/>'
                   f'<text x="{x+3:.1f}" y="{y+9:.1f}" font-size="6" fill="{INK}">{name}</text>')
    return "\n".join(out)


def card(code, v):
    slots = v.get("slots", {})
    name = v.get("name", code)
    return f'''<div class="card">
  <span class="lbl">{code}</span><span class="ttl">{name}</span>
  <div class="viz"><svg viewBox="0 0 {VB_W} {VB_H}">
    <rect x="0" y="0" width="{VB_W}" height="{VB_H}" fill="#fff" stroke="{LINE}"/>
    {slot_rects(slots)}
  </svg></div>
</div>'''


def main():
    arch = LAY.get("archetypes", {})
    cards = "\n".join(card(c, v) for c, v in arch.items()) if arch else \
        '<div class="empty">아직 변종 0개 — PPTX를 흡수해 layouts.json에 추가하세요.</div>'
    html = f'''<!doctype html><html lang="ko"><meta charset="utf-8">
<title>ppt-lab catalog ({len(arch)} variants)</title>
<style>
  body{{font-family:Pretendard,'Malgun Gothic',sans-serif;background:#F8FAFC;margin:0;padding:32px;color:{INK}}}
  h1{{font-size:20px}} .sub{{color:#64748B;font-size:13px;margin-bottom:24px}}
  .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
  .card{{background:#fff;border:1px solid {LINE};border-radius:12px;padding:14px}}
  .lbl{{display:inline-block;background:{BRAND};color:#fff;font-size:11px;font-weight:700;
        padding:2px 8px;border-radius:4px;margin-right:8px}}
  .ttl{{font-size:13px;font-weight:600}}
  .viz{{margin-top:10px}} .viz svg{{width:100%;height:auto;border-radius:6px}}
  .empty{{color:#94A3B8;padding:40px;text-align:center;border:1px dashed {LINE};border-radius:12px}}
</style>
<h1>ppt-lab 카탈로그</h1>
<div class="sub">layouts.json 에서 자동 생성됨 (render-catalog.py) · {len(arch)}개 변종 · 손으로 고치지 말 것</div>
<div class="grid">
{cards}
</div></html>'''
    out = os.path.join(REF, "catalog.html")
    open(out, "w", encoding="utf-8").write(html)
    print(f"[render-catalog] {len(arch)}개 변종 → {out}")


if __name__ == "__main__":
    main()
