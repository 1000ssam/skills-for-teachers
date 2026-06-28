#!/usr/bin/env python3
"""extract-images.py — 사용자 콘텐츠에서 이미지를 떼어내 슬라이드 assets로.

이미지 조달 1순위: 없던 걸 생성/그리기 전에 **사용자가 준 진짜 이미지부터 재활용**한다.
소스에서 이미지를 추출 → `<slides-dir>/assets/extracted/` 에 저장하고, 매니페스트(크기·비율)
를 출력한다. 어느 걸 어느 슬롯에 넣을지는 에이전트가 매니페스트 보고 고르고, **크롭/맞춤은
엔진의 `media()`** 가 `fit:cover|contain` + `focal` 로 처리한다(이 도구는 추출만).

지원 소스(--src, 확장자/스킴 자동 판별):
  PDF(.pdf, PyMuPDF) · PPTX/DOCX/XLSX(zip 내 media) · 폴더 · 단일 이미지 · http(s) URL

기본 필터: 긴 변 < --min-size(기본 200px) 아이콘/불릿류 제외 + 내용 해시 중복 제거.

예:
  python3 extract-images.py --src /mnt/c/dev/원본.pdf  --slides-dir /mnt/c/dev/decks/d
  python3 extract-images.py --src /mnt/c/dev/기획.pptx --out-dir /mnt/c/dev/decks/d/assets/extracted
  python3 extract-images.py --src https://example.com/post --min-size 300
"""
import argparse
import hashlib
import io
import pathlib
import re
import sys
import urllib.parse
import urllib.request
import zipfile

from PIL import Image

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
ZIP_MEDIA = {".pptx": "ppt/media/", ".docx": "word/media/", ".xlsx": "xl/media/",
             ".potx": "ppt/media/", ".key": "", ".odp": "Pictures/"}


def detect(src):
    if re.match(r"^https?://", src):
        return "url"
    p = pathlib.Path(src)
    if not p.exists():
        sys.exit(f"[extract] 소스 없음: {src}")
    if p.is_dir():
        return "dir"
    ext = p.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in ZIP_MEDIA:
        return "zip"
    if ext in IMG_EXT:
        return "image"
    sys.exit(f"[extract] 지원 안 하는 소스 형식: {ext}")


# ---------- 소스별 추출: (bytes, 출처라벨) 목록 ----------
def from_pdf(path):
    import fitz
    out = []
    doc = fitz.open(path)
    for pno in range(len(doc)):
        for img in doc.get_page_images(pno, full=True):
            xref = img[0]
            try:
                d = doc.extract_image(xref)
            except Exception:
                continue
            out.append((d["image"], f"p{pno + 1}#xref{xref}"))
    doc.close()
    return out


def from_zip(path):
    prefix = ZIP_MEDIA.get(pathlib.Path(path).suffix.lower(), "")
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            low = n.lower()
            if (not prefix or low.startswith(prefix)) and pathlib.Path(low).suffix in IMG_EXT:
                out.append((z.read(n), pathlib.Path(n).name))
    return out


def from_dir(path):
    out = []
    for f in sorted(pathlib.Path(path).rglob("*")):
        if f.suffix.lower() in IMG_EXT and f.is_file():
            out.append((f.read_bytes(), f.name))
    return out


def from_image(path):
    return [(pathlib.Path(path).read_bytes(), pathlib.Path(path).name)]


def from_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (extract-images)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)', html, re.I)
    srcs += re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html, re.I)
    seen, out = set(), []
    for s in srcs:
        full = urllib.parse.urljoin(url, s)
        if full in seen or full.startswith("data:"):
            continue
        seen.add(full)
        try:
            rq = urllib.request.Request(full, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(rq, timeout=20) as ir:
                out.append((ir.read(), pathlib.Path(urllib.parse.urlparse(full).path).name or "web"))
        except Exception:
            continue
        if len(out) >= 40:
            break
    return out


EXTRACT = {"pdf": from_pdf, "zip": from_zip, "dir": from_dir, "image": from_image, "url": from_url}


def main():
    ap = argparse.ArgumentParser(description="사용자 콘텐츠에서 이미지 추출 → assets")
    ap.add_argument("--src", required=True, help="PDF/PPTX/DOCX/폴더/이미지/URL")
    ap.add_argument("--out-dir", help="저장 폴더(미지정 시 <slides-dir>/assets/extracted)")
    ap.add_argument("--slides-dir", help="덱 워크스페이스")
    ap.add_argument("--min-size", type=int, default=200, help="긴 변 최소 px(아이콘 제외, 기본 200)")
    args = ap.parse_args()

    kind = detect(args.src)
    raw = EXTRACT[kind](args.src)

    out_dir = pathlib.Path(args.out_dir) if args.out_dir else (
        (pathlib.Path(args.slides_dir) if args.slides_dir else pathlib.Path.cwd()) / "assets" / "extracted")
    out_dir.mkdir(parents=True, exist_ok=True)

    seen_hash, manifest, idx = set(), [], 0
    for data, ref in raw:
        h = hashlib.sha1(data).hexdigest()
        if h in seen_hash:
            continue
        try:
            im = Image.open(io.BytesIO(data))
            w, ht = im.size
            fmt = (im.format or "PNG").lower()
        except Exception:
            continue
        if max(w, ht) < args.min_size:        # 아이콘/불릿류 제외
            continue
        seen_hash.add(h)
        idx += 1
        ext = ".jpg" if fmt in ("jpeg", "jpg") else (f".{fmt}" if f".{fmt}" in IMG_EXT else ".png")
        name = f"img-{idx:02d}{ext}"
        (out_dir / name).write_bytes(data)
        ratio = round(w / ht, 2) if ht else 0
        shape = "와이드" if ratio >= 1.6 else ("세로" if ratio <= 0.7 else ("정사각" if 0.9 <= ratio <= 1.1 else "표준"))
        manifest.append({"file": str(out_dir / name), "w": w, "h": ht,
                         "ratio": ratio, "shape": shape, "src": ref, "kb": len(data) // 1024})

    if not manifest:
        sys.exit(f"[extract] {kind} 소스에서 (min-size {args.min_size}px 이상) 이미지 0개.")

    import json
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    # 사람이 읽는 표 + 슬롯 매칭 힌트
    print(f"[extract] {kind} → {len(manifest)}개 추출 → {out_dir}")
    print(f"{'파일':22} {'크기':>11} {'비율':>5} {'형태':>5}  출처")
    for m in manifest:
        print(f"{pathlib.Path(m['file']).name:22} {m['w']}x{m['h']:<6} {m['ratio']:>5} {m['shape']:>5}  {m['src']}")
    print("→ 슬롯 매칭: 와이드=feature media/배경, 정사각·세로=duo/grid/trio 이미지 카드. "
          "spec 의 src 에 경로 넣고 fit:cover(+focal) 로 크롭.")
    print(f"manifest: {out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
