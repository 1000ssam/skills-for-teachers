"""
수능/모평/학평 기출 문항 개별 크롭 스크립트
모든 수능 과목 대응 (국어, 수학, 영어, 사탐, 과탐, 한국사 등)

Usage:
    python crop_questions.py <exam_dir> <out_dir> <questions_json>

questions_json 형식:
[
  {
    "file": "exam_filename.pdf",
    "exam_name": "2025_3월학평",
    "questions": [
      {"q": 2, "page": 0},
      {"q": 5, "page": -1}
    ]
  }
]

page: 0-based PDF 페이지 인덱스. -1이면 전 페이지 순회하여 자동 탐지.
"""
import fitz
import sys
import os
import json
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

DPI = 200
SCALE = DPI / 72
SAFE_PAD = 8  # 트리밍 후 사방 균일 안전 패딩 (px)


def detect_right_label_x(page):
    """세로 과목 라벨(동아시아사, 물리학Ⅰ 등)의 x 시작점을 동적 감지."""
    pw = page.rect.width
    blocks = page.get_text("dict")
    # 수능 시험지 우측 세로 라벨에 등장하는 글자들
    label_chars = set(
        "동아시사사회탐구영역과학국어수영물리화생지윤한정법경제세계"
        "ⅠⅡ문법언매체작독서확률통계미적분기하"
    )
    min_x = pw
    for b in blocks.get("blocks", []):
        for l in b.get("lines", []):
            for s in l.get("spans", []):
                text = s["text"].strip()
                if (
                    s["bbox"][0] > pw - 100
                    and len(text) <= 3
                    and any(c in label_chars for c in text)
                ):
                    min_x = min(min_x, s["bbox"][0])
    return min_x - 5 if min_x < pw else pw - 55


def find_q_on_page(page, q_num):
    """페이지에서 문항 번호 N.의 위치를 찾는다. 없으면 None."""
    mid_x = page.rect.width / 2
    hits = page.search_for(f"{q_num}.")
    for r in hits:
        check = fitz.Rect(r.x0 - 3, r.y0 - 2, r.x0 + 60, r.y1 + 2)
        text = page.get_text("text", clip=check).strip()
        if text.startswith(f"{q_num}.") and len(text) > 3:
            return r
    return None


def find_last_choice_y(page, is_right, mid_x, y_start):
    """⑤~① 역순으로 마지막 선지의 하단 y를 찾는다."""
    for sym in ["\u2464", "\u2463", "\u2462", "\u2461", "\u2460"]:
        hits = page.search_for(sym)
        candidates = [
            r
            for r in hits
            if (
                (is_right and r.x0 > mid_x - 10)
                or (not is_right and r.x0 < mid_x - 10)
            )
            and r.y0 > y_start + 15
        ]
        if not candidates:
            continue
        best = max(candidates, key=lambda r: r.y0)
        return best.y1 + 2
    return None


def find_q_clip(page, q_num, label_x):
    """문항의 PDF 클리핑 영역을 계산한다."""
    pw = page.rect.width
    ph = page.rect.height
    mid_x = pw / 2

    q_rect = find_q_on_page(page, q_num)
    if q_rect is None:
        return None

    next_hits = page.search_for(f"{q_num + 1}.")

    is_right = q_rect.x0 > mid_x - 10
    y_start = q_rect.y0 - 8

    # y_end: 같은 컬럼의 다음 문항 or 마지막 선지
    y_end = None
    for r in next_hits:
        same_col = (is_right and r.x0 > mid_x - 10) or (
            not is_right and r.x0 < mid_x - 10
        )
        if same_col and r.y0 > y_start + 20:
            check = fitz.Rect(r.x0 - 3, r.y0 - 2, r.x0 + 60, r.y1 + 2)
            text = page.get_text("text", clip=check).strip()
            if text.startswith(f"{q_num + 1}.") and len(text) > 3:
                y_end = r.y0 - 5
                break
    if y_end is None:
        last_y = find_last_choice_y(page, is_right, mid_x, y_start)
        y_end = last_y if last_y else ph - 60

    # x 범위: 넉넉하게 잡되 세로 라벨만 제외
    if is_right:
        x0 = mid_x - 3
        x1 = label_x
    else:
        x0 = q_rect.x0 - 15
        x1 = mid_x + 3

    return fitz.Rect(x0, y_start, x1, y_end)


def trim_and_pad(img, pad=SAFE_PAD):
    """흰 여백 트리밍 후 사방 균일 패딩 추가."""
    arr = np.array(img)
    mask = np.any(arr < 250, axis=2)
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any():
        return img
    y0, y1 = np.where(rows)[0][[0, -1]]
    x0, x1 = np.where(cols)[0][[0, -1]]
    cropped = img.crop((x0, y0, x1 + 1, y1 + 1))
    w, h = cropped.size
    padded = Image.new("RGB", (w + pad * 2, h + pad * 2), (255, 255, 255))
    padded.paste(cropped, (pad, pad))
    return padded


def find_page_for_question(doc, q_num):
    """전 페이지를 순회하여 문항이 있는 페이지 인덱스를 반환."""
    for i in range(doc.page_count):
        if find_q_on_page(doc[i], q_num) is not None:
            return i
    return None


def main():
    if len(sys.argv) != 4:
        print("Usage: python crop_questions.py <exam_dir> <out_dir> <questions_json>")
        sys.exit(1)

    exam_dir = sys.argv[1]
    out_dir = sys.argv[2]
    questions_json = sys.argv[3]

    with open(questions_json, "r", encoding="utf-8") as f:
        exams = json.load(f)

    os.makedirs(out_dir, exist_ok=True)

    saved = []
    for exam in exams:
        fname = exam["file"]
        exam_name = exam["exam_name"]
        path = os.path.join(exam_dir, fname)

        if not os.path.exists(path):
            print(f"SKIP: {path} not found")
            continue

        doc = fitz.open(path)

        for item in exam["questions"]:
            q_num = item["q"]
            pg_idx = item["page"]

            # page: -1이면 전 페이지 순회
            if pg_idx < 0:
                pg_idx = find_page_for_question(doc, q_num)
                if pg_idx is None:
                    print(f"SKIP: {exam_name} Q{q_num} - 문항 못 찾음")
                    continue

            page = doc[pg_idx]
            label_x = detect_right_label_x(page)
            clip = find_q_clip(page, q_num, label_x)

            if clip is None:
                print(f"SKIP: {exam_name} Q{q_num} - 영역 못 찾음")
                continue

            mat = fitz.Matrix(SCALE, SCALE)
            pix = page.get_pixmap(matrix=mat, clip=clip)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = trim_and_pad(img)

            out_name = f"{exam_name}_Q{q_num:02d}.webp"
            out_path = os.path.join(out_dir, out_name)
            img.save(out_path, "WEBP", quality=88)

            size_kb = os.path.getsize(out_path) / 1024
            saved.append(out_name)
            print(f"OK: {out_name} ({img.width}x{img.height}, {size_kb:.0f}KB)")

        doc.close()

    print(f"\n총 {len(saved)}개 저장: {os.path.abspath(out_dir)}")


if __name__ == "__main__":
    main()
