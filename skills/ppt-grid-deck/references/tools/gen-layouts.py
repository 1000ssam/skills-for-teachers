#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen-layouts.py — grid.json(SSOT) → layouts.json 생성기.

archetypes.md 의 24개 아키타입 슬롯 명세(grid:[c0,cspan,r0,rspan])를 결정론적으로
grid_box() 로 해소해 픽셀 좌표 layouts.json 을 찍어낸다. 매직넘버 금지 — 모든 좌표는
grid.json 에서 파생. h_override / y_offset 은 grid.json 의 header/footer 밴드 규칙과
동일하게 적용한다.

Usage:
  python3 gen-layouts.py            # references/layouts.json 갱신

산출 구조:
  layouts.json = {
    "_meta": {... + header_band/footer_band 해소값},
    "grid": {... 원본 grid 수치 ...},
    "archetypes": { "<slug>": { "family":..., "header": bool, "bg":opt,
                                "slots": { "<name>": [x,y,w,h], ... } } },
    "chart_region": { ... 데이터 패밀리 차트 영역 별칭 ... }
  }
"""
import json
import os
import collections

REF = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID = json.load(open(os.path.join(REF, "grid.json"), encoding="utf-8"))

COLS = GRID["columns"]
ROWS = GRID["rows"]
ORIGIN_X = COLS["origin_x"]
COL_W = COLS["col_w"]
COL_PITCH = COLS["col_pitch"]
GUTTER = COLS["gutter"]
ORIGIN_Y = ROWS["origin_y"]
ROW_H = ROWS["row_h"]
ROW_PITCH = ROWS["row_pitch"]
ROW_GUTTER = ROWS["gutter"]


def grid_box(c0, cspan, r0, rspan):
    """grid.json _meta.derivation 그대로. 정수 px.
    x=origin_x + c0*col_pitch
    w=cspan*col_w + (cspan-1)*gutter
    y=origin_y + r0*row_pitch
    h=rspan*row_h + (rspan-1)*row_gutter
    """
    x = ORIGIN_X + c0 * COL_PITCH
    w = cspan * COL_W + (cspan - 1) * GUTTER
    y = ORIGIN_Y + r0 * ROW_PITCH
    h = rspan * ROW_H + (rspan - 1) * ROW_GUTTER
    return [int(x), int(y), int(w), int(h)]


def resolve_band_slot(spec):
    """header_band / footer_band 슬롯 해소.
    grid:[c0,cspan,r0,rspan] 로 base box 를 구한 뒤,
    h_override 가 있으면 h 를 교체, y_offset 이 있으면 y 에 더한다(baseline 미세조정)."""
    c0, cspan, r0, rspan = spec["grid"]
    box = grid_box(c0, cspan, r0, rspan)
    if "y_offset" in spec:
        box[1] += int(spec["y_offset"])
    if "h_override" in spec:
        box[3] = int(spec["h_override"])
    return box


# ---------------------------------------------------------------------------
# 24 아키타입 슬롯 명세 — archetypes.md 에서 인코딩.
# 각 슬롯 = grid:[c0,cspan,r0,rspan] (+ 선택적 h_override/y_offset).
# 패밀리/헤더밴드 사용여부/배경(bg)도 함께 기록.
# 동적 슬롯(items[]/cells[]/steps[] 등)은 컨테이너 영역 1개로 기록하고
# 빌드 함수가 박스를 N분할한다(분할은 build-template.py 의 책임 — explicit).
# ---------------------------------------------------------------------------
ARCHETYPES = collections.OrderedDict()


def A(slug, family, slots, header=False, bg=None, notes=None):
    entry = {"family": family, "header": header}
    if bg:
        entry["bg"] = bg
    if notes:
        entry["_notes"] = notes
    resolved = collections.OrderedDict()
    for name, spec in slots.items():
        if isinstance(spec, dict):           # 밴드형(override/offset 포함)
            resolved[name] = resolve_band_slot(spec)
        else:                                 # [c0,cspan,r0,rspan]
            resolved[name] = grid_box(*spec)
    entry["slots"] = resolved
    ARCHETYPES[slug] = entry


# ---- Family 1: Frame (헤더밴드 미사용 / 전면 구도) ------------------------
A("cover", "Frame", {
    "kicker":   [0, 8, 1, 1],
    "title":    [0, 11, 2, 3],
    "subtitle": [0, 9, 5, 1],
    "meta":     [0, 9, 7, 1],
}, header=False, bg="canvas",
   notes="덱 오프닝. bg/색은 룩·팔레트가 결정(canvas=룩 캔버스). 선택적 풀블리드 배경 이미지.")

A("section", "Frame", {
    "index":         [0, 2, 1, 1],
    "section_title": [0, 10, 3, 2],
    "caption":       [0, 8, 5, 1],
}, header=False, bg="canvas",
   notes="섹션 전환. 선택적 사이드/풀블리드 배경 이미지.")

A("agenda", "Frame", {
    "kicker": [0, 6, 0, 1],
    "title":  [0, 10, 1, 1],
    "items":  [0, 12, 3, 4],   # 컨테이너 — 행 분배는 빌드 함수
}, header=False,
   notes="목차. items 컨테이너를 항목 수만큼 행 분배(번호/불릿).")

A("closing", "Frame", {
    "kicker":   [0, 8, 1, 1],
    "title":    [0, 11, 2, 2],
    "subtitle": [0, 9, 4, 1],
    "cta":      [0, 4, 6, 1],
}, header=False, bg="canvas",
   notes="마무리/CTA.")

# ---- Family 2: Focus (헤더밴드 사용) --------------------------------------
A("statement", "Focus", {
    "lead":    [0, 9, 2, 2],   # body_top 행부터 2행 — 풀쿼트(헤더 h2와 구분되는 h1)
    "support": [0, 11, 4, 3],  # 근거 컨테이너(키운 lead 아래로 한 행 이동)
    "image":   [7, 5, 4, 3],   # 선택적 보조 이미지(미디어 슬롯, support 와 정렬)
}, header=True,
   notes="한 주장(lead=풀쿼트, 좌측 액센트 바+h1) + 근거. image 는 선택적 보조 미디어.")

A("feature", "Focus", {
    "body":  [0, 6, 2, 4],
    "media": [7, 5, 2, 5],     # 히어로 비주얼(미디어 슬롯, 큰 1장)
}, header=True,
   notes="히어로 비주얼 + 인사이트. media=media() 헬퍼.")

A("showcase", "Focus", {
    "media": [0, 12, 2, 5],    # 풀폭 와이드 미디어(스크린샷/UI/도표) — 12컬럼 전폭
}, header=True,
   notes="와이드 단일 미디어 전폭 전시. 기본 fit=contain(안 잘림·원본 비율) — 가이드/UI 캡처·도표용. 캡션은 media.caption.")

# ---- Family 3: Set (헤더밴드 사용 / 동등 카드) ----------------------------
A("duo", "Set", {
    "item_l": [0, 6, 2, 5],
    "item_r": [6, 6, 2, 5],
}, header=True,
   notes="2 동등 항목. 각 카드 상단에 선택적 이미지 밴드(이미지 카드 변종).")

A("trio", "Set", {
    "col1": [0, 4, 2, 5],
    "col2": [4, 4, 2, 5],
    "col3": [8, 4, 2, 5],
}, header=True,
   notes="3 동등 항목. 카드별 선택적 이미지 밴드.")

A("grid", "Set", {
    # 4~6 카드: 2행 × (2 또는 3열). 컨테이너 1개를 빌드 함수가 분할.
    "cells": [0, 12, 2, 5],
}, header=True,
   notes="4~6 카드(2×2 또는 2×3). cells 컨테이너를 카드 수에 맞춰 분할. 카드별 선택적 이미지.")

A("list", "Set", {
    "items": [0, 12, 2, 5],
}, header=True,
   notes="순차 리스트/메뉴. items 컨테이너 행 분배(번호/불릿).")

# ---- Family 4: Contrast (명시적 비교) -------------------------------------
A("versus", "Contrast", {
    "left":  [0, 6, 2, 5],
    "right": [6, 6, 2, 5],
}, header=True,
   notes="A vs B / Before·After. 중앙 vs 마크는 빌드 함수가 두 박스 사이에 배치.")

A("matrix", "Contrast", {
    "table": [0, 12, 2, 5],
}, header=True,
   notes="기준×옵션 표. 헤더행 + N행은 빌드 함수가 table 박스를 분할.")

A("rank", "Contrast", {
    "rows": [0, 10, 2, 5],
}, header=True,
   notes="서열/변동. rows 컨테이너 행 분배(rank/label/delta).")

# ---- Family 5: Field (2축 공간 배치) --------------------------------------
A("quadrant", "Field", {
    "cells": [0, 12, 2, 5],   # 2×2 분할은 빌드 함수
}, header=True,
   notes="범주 2×2. cells 를 2×2 분할. x_axis/y_axis 라벨은 빌드 함수가 박스 가장자리에.")

A("map", "Field", {
    "plot": [0, 9, 2, 5],     # 연속 2축 플롯 영역
}, header=True,
   notes="연속 2축 포지셔닝. points{x,y:0~1}를 plot 박스 안에 배치. 축라벨은 가장자리.")

# ---- Family 6: Structure (과정 / 구조) ------------------------------------
A("flow", "Structure", {
    "steps": [0, 12, 3, 3],   # 가로 분배 + 커넥터는 빌드 함수
}, header=True,
   notes="순서/단계/타임라인. steps 컨테이너 가로 N분배 + 커넥터.")

A("system", "Structure", {
    "core":  [4, 4, 4, 2],    # 중심
    "nodes": [0, 12, 2, 5],   # 코어 주위 노드 배치 영역(그리드 셀 파생)
}, header=True,
   notes="아키텍처/계층. core 중심 + nodes 영역에 코어 주위로 배치(오빗수학 폐기·그리드 파생).")

# ---- Family 7: Data (Zelazny 5비교유형 + KPI) -----------------------------
A("share", "Data", {
    "chart":  [0, 7, 2, 5],
    "legend": [8, 4, 2, 5],
}, header=True,
   notes="구성. 파이/도넛/누적. chart=chart() 헬퍼.")

A("bars", "Data", {
    "chart": [0, 12, 2, 5],
}, header=True, notes="항목. 가로/세로 바.")

A("trend", "Data", {
    "chart": [0, 12, 2, 5],
}, header=True, notes="시계열. 라인/세로열.")

A("spread", "Data", {
    "chart": [0, 12, 2, 5],
}, header=True, notes="빈도. 히스토그램.")

A("correlate", "Data", {
    "chart": [0, 10, 2, 5],
}, header=True, notes="상관. 스캐터/버블.")

A("kpi", "Data", {
    "cells": [0, 12, 2, 3],   # 가로 N분할 빅넘버 카드
}, header=True,
   notes="다수 단일지표. cells 컨테이너 가로 N분할 빅넘버 카드.")


# ---------------------------------------------------------------------------
# 차트 영역 별칭(데이터 패밀리 chart() 헬퍼 참조용).
# 헤더밴드 아래 body_top(row2) 부터 시작하는 표준 차트 영역.
# ---------------------------------------------------------------------------
CHART_REGION = {
    "full":        grid_box(0, 12, 2, 5),   # 전폭 차트
    "with_legend": grid_box(0, 7, 2, 5),    # share 차트부
    "legend":      grid_box(8, 4, 2, 5),    # share 범례부
    "kpi_row":     grid_box(0, 12, 2, 3),   # kpi 빅넘버 행
}


def build_meta():
    hb = GRID["header_band"]
    fb = GRID["footer_band"]
    meta = collections.OrderedDict()
    meta["generated"] = ("generated from grid.json — do not hand-edit; "
                         "edit grid.json or gen-layouts.py")
    meta["canvas"] = GRID["_meta"]["canvas"]
    meta["baseline"] = GRID["_meta"]["baseline"]
    meta["margin"] = GRID["margin"]
    # 헤더밴드 해소(kicker/title/divider) — 빌드 함수 header() 가 참조
    meta["header_band"] = collections.OrderedDict()
    for k in ("kicker", "title", "divider"):
        meta["header_band"][k] = resolve_band_slot(hb[k])
    meta["header_band"]["body_top_y"] = ORIGIN_Y + hb["body_top_row"] * ROW_PITCH
    # 푸터밴드 해소(caption/pageno)
    meta["footer_band"] = collections.OrderedDict()
    for k in ("caption", "pageno"):
        meta["footer_band"][k] = resolve_band_slot(fb[k])
    meta["footer_band"]["pageno_align"] = fb["pageno"].get("align", "right")
    return meta


def main():
    out = collections.OrderedDict()
    out["_meta"] = build_meta()
    out["grid"] = {
        "columns": COLS, "rows": ROWS,
        "_derivation": GRID["_meta"]["derivation"],
    }
    out["archetypes"] = ARCHETYPES
    out["chart_region"] = CHART_REGION
    path = os.path.join(REF, "layouts.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[gen-layouts] {len(ARCHETYPES)}개 아키타입 → {path}")
    # 무결성 체크: 모든 슬롯 박스가 캔버스 안에 있는지 경고
    cw, chgt = GRID["_meta"]["canvas"]["w"], GRID["_meta"]["canvas"]["h"]
    for slug, e in ARCHETYPES.items():
        for name, (x, y, w, h) in e["slots"].items():
            if x < 0 or y < 0 or x + w > cw or y + h > chgt:
                print(f"  ⚠ {slug}.{name} 캔버스 초과: [{x},{y},{w},{h}]")


if __name__ == "__main__":
    main()
