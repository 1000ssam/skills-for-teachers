"""
수능/모평/학평 기출 문항 개별 크롭 스크립트
모든 수능 과목 대응 (국어, 수학, 영어, 사탐, 과탐, 한국사 등)

== 분석 모드 (특정 문항만 크롭) ==
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

== 분할 모드 (전체 문항 자동 분할) ==
    python crop_questions.py --split <pdf_or_dir> <out_dir>

PDF 파일 또는 폴더를 지정하면 모든 문항을 자동 감지하여 개별 크롭한다.
시험명은 PDF 내부 텍스트에서 자동 식별한다.
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


def identify_exam_name(doc, filepath=""):
    """PDF 텍스트 또는 파일명에서 시험명을 자동 식별한다."""
    import re

    # 전체 페이지 텍스트를 모아서 탐색
    all_text = ""
    for i in range(min(doc.page_count, 4)):
        all_text += doc[i].get_text()
    text = all_text[:3000]

    # 학년도 추출
    year_match = re.search(r"(20\d{2})학년도", text)
    year = year_match.group(1) if year_match else ""

    # 시험 유형 판별
    exam_type = ""
    if "6월" in text and ("모의평가" in text or "모평" in text):
        exam_type = "6월모평"
    elif "9월" in text and ("모의평가" in text or "모평" in text):
        exam_type = "9월모평"
    elif "대학수학능력시험" in text and "6월" not in text and "9월" not in text:
        exam_type = "수능"
    elif "전국연합학력평가" in text or ("학력평가" in text and "사회탐구" not in text[:30]):
        month_match = re.search(r"(\d{1,2})월", text[:500])
        month = month_match.group(1) if month_match else ""
        exam_type = f"{month}월학평" if month else "학평"
    elif "고3" in text:
        month_match = re.search(r"(\d{1,2})월", text[:500])
        month = month_match.group(1) if month_match else ""
        exam_type = f"{month}월학평" if month else "교육청"

    # 텍스트에서 식별 실패 시 파일명 폴백
    if not exam_type and filepath:
        fname = os.path.splitext(os.path.basename(filepath))[0]
        if "수능" in fname:
            exam_type = "수능"
        elif "6월" in fname:
            exam_type = "6월모평"
        elif "9월" in fname:
            exam_type = "9월모평"
        else:
            exam_type = fname.replace(" ", "_")

    if not year and filepath:
        fname = os.path.basename(filepath)
        year_match = re.search(r"(20\d{2})", fname)
        year = year_match.group(1) if year_match else ""

    if not exam_type:
        exam_type = "시험"

    return f"{year}_{exam_type}" if year else exam_type


def detect_all_questions(doc):
    """PDF 전체에서 존재하는 모든 문항 번호와 페이지를 탐지한다."""
    found = {}
    for pg_idx in range(doc.page_count):
        page = doc[pg_idx]
        for q_num in range(1, 51):  # 최대 50번까지 탐색
            if q_num in found:
                continue
            if find_q_on_page(page, q_num) is not None:
                found[q_num] = pg_idx
    return found


def crop_and_save(doc, pg_idx, q_num, exam_name, out_dir):
    """단일 문항을 크롭하여 저장한다. 성공 시 파일명 반환, 실패 시 None."""
    page = doc[pg_idx]
    label_x = detect_right_label_x(page)
    clip = find_q_clip(page, q_num, label_x)

    label = exam_name or os.path.basename(out_dir)
    if clip is None:
        print(f"SKIP: {label} Q{q_num} - 영역 못 찾음")
        return None

    mat = fitz.Matrix(SCALE, SCALE)
    pix = page.get_pixmap(matrix=mat, clip=clip)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img = trim_and_pad(img)

    if exam_name:
        out_name = f"{exam_name}_Q{q_num:02d}.webp"
    else:
        out_name = f"Q{q_num:02d}.webp"
    out_path = os.path.join(out_dir, out_name)
    img.save(out_path, "WEBP", quality=88)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"OK: {out_name} ({img.width}x{img.height}, {size_kb:.0f}KB)")
    return out_name


def run_analysis_mode(exam_dir, out_dir, questions_json):
    """분석 모드: JSON으로 지정된 특정 문항만 크롭."""
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

            if pg_idx < 0:
                pg_idx = find_page_for_question(doc, q_num)
                if pg_idx is None:
                    print(f"SKIP: {exam_name} Q{q_num} - 문항 못 찾음")
                    continue

            result = crop_and_save(doc, pg_idx, q_num, exam_name, out_dir)
            if result:
                saved.append(result)

        doc.close()

    print(f"\n총 {len(saved)}개 저장: {os.path.abspath(out_dir)}")


def run_split_mode(pdf_or_dir):
    """분할 모드: PDF의 모든 문항을 자동 감지하여 개별 크롭."""
    # 입력이 파일인지 폴더인지 판별
    pdf_paths = []
    if os.path.isfile(pdf_or_dir) and pdf_or_dir.lower().endswith(".pdf"):
        pdf_paths.append(pdf_or_dir)
        base_dir = os.path.dirname(pdf_or_dir)
    elif os.path.isdir(pdf_or_dir):
        base_dir = pdf_or_dir
        for f in sorted(os.listdir(pdf_or_dir)):
            if f.lower().endswith(".pdf"):
                pdf_paths.append(os.path.join(pdf_or_dir, f))
        # 하위 폴더도 탐색
        for root, dirs, files in os.walk(pdf_or_dir):
            for f in sorted(files):
                full = os.path.join(root, f)
                if f.lower().endswith(".pdf") and full not in pdf_paths:
                    pdf_paths.append(full)
    else:
        print(f"ERROR: '{pdf_or_dir}'는 PDF 파일 또는 폴더가 아닙니다.")
        sys.exit(1)

    if not pdf_paths:
        print(f"ERROR: '{pdf_or_dir}'에서 PDF 파일을 찾을 수 없습니다.")
        sys.exit(1)

    total_saved = []
    for path in pdf_paths:
        doc = fitz.open(path)
        exam_name = identify_exam_name(doc, path)

        # 출력 폴더: 입력의 부모 디렉토리에 시험명 폴더 생성
        out_dir = os.path.join(base_dir, exam_name)
        os.makedirs(out_dir, exist_ok=True)

        print(f"\n=== {os.path.basename(path)} → {exam_name}/ ===")

        questions = detect_all_questions(doc)
        if not questions:
            print(f"  문항을 찾을 수 없습니다.")
            doc.close()
            continue

        print(f"  {len(questions)}개 문항 감지: Q{min(questions)}~Q{max(questions)}")

        for q_num in sorted(questions.keys()):
            pg_idx = questions[q_num]
            result = crop_and_save(doc, pg_idx, q_num, "", out_dir)
            if result:
                total_saved.append(os.path.join(exam_name, result))

        doc.close()

    print(f"\n총 {len(total_saved)}개 저장: {os.path.abspath(base_dir)}")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--split":
        if len(sys.argv) != 3:
            print("Usage: python crop_questions.py --split <pdf_or_dir>")
            sys.exit(1)
        run_split_mode(sys.argv[2])
    elif len(sys.argv) == 4 and sys.argv[1] != "--split":
        run_analysis_mode(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Usage:")
        print("  분석 모드: python crop_questions.py <exam_dir> <out_dir> <questions.json>")
        print("  분할 모드: python crop_questions.py --split <pdf_or_dir>")
        sys.exit(1)


if __name__ == "__main__":
    main()
