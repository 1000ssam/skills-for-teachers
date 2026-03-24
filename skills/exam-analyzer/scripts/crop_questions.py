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
    python crop_questions.py --split <pdf_or_dir>

PDF 파일 또는 폴더를 지정하면 모든 문항을 자동 감지하여 개별 크롭한다.
폴더 지정 시 각 PDF를 병렬로 처리한다.
시험명은 PDF 내부 텍스트에서 자동 식별한다.
"""
import fitz
import sys
import os
import re
import json
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8")

DPI = 200
SCALE = DPI / 72
SAFE_PAD = 8  # 트리밍 후 사방 균일 안전 패딩 (px)
COL_TOLERANCE = 20  # 컬럼 기준점으로부터 허용 오차 (pt)


def detect_right_label_x(page):
    """세로 과목 라벨(동아시아사, 물리학Ⅰ 등)의 x 시작점을 동적 감지."""
    pw = page.rect.width
    blocks = page.get_text("dict")
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


def _raw_search_q(page, q_num):
    """x 필터 없이 페이지에서 문항 번호 N.의 모든 후보를 반환."""
    results = []
    hits = page.search_for(f"{q_num}.")
    for r in hits:
        check = fitz.Rect(r.x0 - 3, r.y0 - 2, r.x0 + 60, r.y1 + 2)
        text = page.get_text("text", clip=check).strip()
        if text.startswith(f"{q_num}.") and len(text) > 3:
            results.append(r)
    return results


def detect_column_baselines(doc):
    """PDF에서 실제 문항 번호의 x좌표를 수집하여 좌/우 컬럼 기준점을 결정."""
    mid_x = doc[0].rect.width / 2
    left_xs = []
    right_xs = []

    # Q1~Q10까지 탐색하여 x좌표 수집
    for pg_idx in range(doc.page_count):
        page = doc[pg_idx]
        for q_num in range(1, 11):
            candidates = _raw_search_q(page, q_num)
            for r in candidates:
                if r.x0 < mid_x:
                    left_xs.append(r.x0)
                else:
                    right_xs.append(r.x0)

    # 각 컬럼에서 가장 빈번한 x좌표 근처를 기준점으로 사용
    left_base = _find_cluster_center(left_xs) if left_xs else None
    right_base = _find_cluster_center(right_xs) if right_xs else mid_x + 10

    return left_base, right_base


def _find_cluster_center(xs):
    """x좌표 리스트에서 가장 많이 모인 클러스터의 중심을 반환."""
    if not xs:
        return None
    # 가장 작은 값 근처에 클러스터가 있을 가능성이 높음 (컬럼 시작점)
    xs_sorted = sorted(xs)
    best_center = xs_sorted[0]
    best_count = 0
    for x in xs_sorted:
        count = sum(1 for v in xs if abs(v - x) < COL_TOLERANCE)
        if count > best_count:
            best_count = count
            best_center = x
    return best_center


def find_q_on_page(page, q_num, baselines=None):
    """페이지에서 문항 번호 N.의 위치를 찾는다. 없으면 None."""
    candidates = _raw_search_q(page, q_num)
    if not candidates:
        return None

    if baselines is None:
        # 폴백: 첫 번째 후보 반환 (분석 모드)
        return candidates[0]

    left_base, right_base = baselines

    # 기준점에 가까운 후보만 통과
    for r in candidates:
        if left_base is not None and abs(r.x0 - left_base) < COL_TOLERANCE:
            return r
        if right_base is not None and abs(r.x0 - right_base) < COL_TOLERANCE:
            return r

    return None


def find_last_choice_y(page, is_right, mid_x, y_start):
    """⑤~① 역순으로 마지막 선지의 하단 y를 찾는다.
    선지 텍스트(여러 줄) 및 이미지(그래프/지도) 모두 고려."""
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
        col_x0 = mid_x - 5 if is_right else 0
        col_x1 = page.rect.width if is_right else mid_x + 5
        # 텍스트 + 이미지 블록 모두 스캔하여 실제 콘텐츠 하단을 찾음
        scan_rect = fitz.Rect(col_x0, best.y0, col_x1, best.y0 + 120)
        blocks = page.get_text("dict", clip=scan_rect)
        last_y1 = best.y1
        for b in blocks.get("blocks", []):
            # 이미지 블록 (type=1)
            if b.get("type") == 1:
                if b["bbox"][3] > last_y1:
                    last_y1 = b["bbox"][3]
            # 텍스트 블록 (type=0)
            else:
                for ln in b.get("lines", []):
                    for s in ln.get("spans", []):
                        if s["bbox"][3] > last_y1:
                            last_y1 = s["bbox"][3]
        return last_y1 + 4
    return None


def find_q_clip(page, q_num, label_x, baselines=None):
    """문항의 PDF 클리핑 영역을 계산한다."""
    pw = page.rect.width
    ph = page.rect.height
    mid_x = pw / 2

    q_rect = find_q_on_page(page, q_num, baselines)
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
            # 다음 문항 후보도 컬럼 기준점 필터 적용
            if baselines:
                left_base, right_base = baselines
                near_left = left_base is not None and abs(r.x0 - left_base) < COL_TOLERANCE
                near_right = right_base is not None and abs(r.x0 - right_base) < COL_TOLERANCE
                if not (near_left or near_right):
                    continue
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


def find_page_for_question(doc, q_num, baselines=None):
    """전 페이지를 순회하여 문항이 있는 페이지 인덱스를 반환."""
    for i in range(doc.page_count):
        if find_q_on_page(doc[i], q_num, baselines) is not None:
            return i
    return None


def identify_exam_name(doc, filepath=""):
    """PDF 텍스트 또는 파일명에서 시험명을 자동 식별한다."""
    # 전체 페이지 텍스트를 모아서 탐색
    all_text = ""
    for i in range(min(doc.page_count, 4)):
        all_text += doc[i].get_text()
    text = all_text[:3000]

    # 학년도 추출
    year_match = re.search(r"(20\d{2})학년도", text)
    year = year_match.group(1) if year_match else ""

    # 과목명 추출 (파일명에서)
    subject = ""
    if filepath:
        fname = os.path.basename(filepath)
        subj_match = re.search(r"[((]([^)）]+)[)）]", fname)
        if subj_match:
            subject = subj_match.group(1)

    # 시험 유형 판별
    exam_type = ""
    if "6월" in text and ("모의평가" in text or "모평" in text):
        exam_type = "6월모평"
    elif "9월" in text and ("모의평가" in text or "모평" in text):
        exam_type = "9월모평"
    elif "대학수학능력시험" in text and "6월" not in text and "9월" not in text:
        exam_type = "수능"
    elif "전국연합학력평가" in text or ("학력평가" in text and "사회탐구" not in text[:30]):
        month = ""
        kw = "전국연합학력평가"
        if kw in text:
            kw_idx = text.index(kw)
            nearby = text[max(0, kw_idx - 200) : kw_idx + 200]
            month_match = re.search(r"(\d{1,2})월", nearby)
            month = month_match.group(1) if month_match else ""
        if not month and filepath:
            fname = os.path.basename(filepath)
            month_match = re.search(r"(\d{1,2})월", fname)
            month = month_match.group(1) if month_match else ""
        if not month:
            month_match = re.search(r"(\d{1,2})월", text[:2000])
            month = month_match.group(1) if month_match else ""
        exam_type = f"{month}월학평" if month else "학평"
    elif "고3" in text:
        month = ""
        if filepath:
            fname = os.path.basename(filepath)
            month_match = re.search(r"(\d{1,2})월", fname)
            month = month_match.group(1) if month_match else ""
        if not month:
            month_match = re.search(r"(\d{1,2})월", text[:2000])
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

    # 과목명이 있으면 포함
    parts = []
    if year:
        parts.append(year)
    parts.append(exam_type)
    if subject:
        parts.append(subject)
    return "_".join(parts)


def detect_all_questions(doc, baselines=None):
    """PDF 전체에서 존재하는 모든 문항 번호와 페이지를 탐지한다."""
    found = {}
    for pg_idx in range(doc.page_count):
        page = doc[pg_idx]
        for q_num in range(1, 51):  # 최대 50번까지 탐색
            if q_num in found:
                continue
            if find_q_on_page(page, q_num, baselines) is not None:
                found[q_num] = pg_idx
    return found


def crop_and_save(doc, pg_idx, q_num, exam_name, out_dir, baselines=None):
    """단일 문항을 크롭하여 저장한다. 성공 시 파일명 반환, 실패 시 None."""
    page = doc[pg_idx]
    label_x = detect_right_label_x(page)
    clip = find_q_clip(page, q_num, label_x, baselines)

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


def process_single_pdf(path, base_dir):
    """단일 PDF를 처리한다. 병렬 실행용 워커 함수."""
    doc = fitz.open(path)
    exam_name = identify_exam_name(doc, path)

    out_dir = os.path.join(base_dir, exam_name)
    os.makedirs(out_dir, exist_ok=True)

    # 동적 컬럼 기준점 감지
    baselines = detect_column_baselines(doc)
    left_base, right_base = baselines
    baseline_info = f"L={left_base:.1f}" if left_base else "L=none"
    baseline_info += f", R={right_base:.1f}" if right_base else ", R=none"

    print(f"\n=== {os.path.basename(path)} → {exam_name}/ ({baseline_info}) ===")

    questions = detect_all_questions(doc, baselines)
    if not questions:
        print(f"  문항을 찾을 수 없습니다.")
        doc.close()
        return []

    print(f"  {len(questions)}개 문항 감지: Q{min(questions)}~Q{max(questions)}")

    saved = []
    for q_num in sorted(questions.keys()):
        pg_idx = questions[q_num]
        result = crop_and_save(doc, pg_idx, q_num, "", out_dir, baselines)
        if result:
            saved.append(os.path.join(exam_name, result))

    doc.close()
    return saved


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
        baselines = detect_column_baselines(doc)

        for item in exam["questions"]:
            q_num = item["q"]
            pg_idx = item["page"]

            if pg_idx < 0:
                pg_idx = find_page_for_question(doc, q_num, baselines)
                if pg_idx is None:
                    print(f"SKIP: {exam_name} Q{q_num} - 문항 못 찾음")
                    continue

            result = crop_and_save(doc, pg_idx, q_num, exam_name, out_dir, baselines)
            if result:
                saved.append(result)

        doc.close()

    print(f"\n총 {len(saved)}개 저장: {os.path.abspath(out_dir)}")


def run_split_mode(pdf_or_dir):
    """분할 모드: PDF의 모든 문항을 자동 감지하여 개별 크롭."""
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

    if len(pdf_paths) == 1:
        # 단일 파일: 직접 처리
        total_saved = process_single_pdf(pdf_paths[0], base_dir)
    else:
        # 복수 파일: 병렬 처리
        max_workers = min(len(pdf_paths), os.cpu_count() or 4)
        print(f"PDF {len(pdf_paths)}개를 {max_workers} 워커로 병렬 처리합니다.")
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single_pdf, path, base_dir): path
                for path in pdf_paths
            }
            for future in as_completed(futures):
                path = futures[future]
                try:
                    saved = future.result()
                    total_saved.extend(saved)
                except Exception as e:
                    print(f"ERROR: {os.path.basename(path)} - {e}")

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
