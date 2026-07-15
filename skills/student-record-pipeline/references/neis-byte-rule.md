# NEIS 바이트 규칙 (고정 상수)

생기부 분량은 NEIS 바이트 카운터가 진실이다. LLM이 눈대중으로 세지 않는다 —
`neis_bytes.py`로 **결정론적** 계산.

## 규칙 (기재요령 2026 고등판 p.214 각주 — 공식 명시)
> "교육정보시스템에서 입력 글자의 단위는 Byte이며, **한글 1자는 3Byte, 영문·숫자 1자는 1Byte, 엔터(Enter)는 1Byte**임."
- 한글·한자·전각문자 = **3 byte**
- 영문·숫자·공백·반각 문장부호(ASCII) = **1 byte**
- 개행(엔터) = **1 byte** (공식). 서드파티 계산기 중 2로 세는 것도 있으나 기재요령 규정은 1.
- 세특은 통상 단일 문단이라 개행이 거의 없음. 붙여넣기 직전 실제 입력창 카운터로 최종 확인 권장.

## 참고 환산
- 500 byte ≈ 한글 약 165자 (공백 포함, 순한글 기준)
- 650 byte ≈ 한글 약 215자
- 과목별 세특 상한(관행) = 500자 = 약 1500 byte

## 스크립트
`references/neis_bytes.py` — 파일/폴더/stdin 입력, `--max/--min` 예산 판정, `--json` 지원.
```bash
python3 neis_bytes.py out/ --max 650 --min 500      # 배치 검증
echo "본문" | python3 neis_bytes.py                  # 단건
```
계산식(요지): `\r\n→\n` 정규화 후, 개행=`--newline-bytes`(기본1), ASCII=1, 그 외=3.

## 출처
- **1차(공식):** 2026학년도 학교생활기록부 기재요령(고등학교) 참고자료8, p.214 각주 → `references/giwan-2026-grounding.md` §3.
- 참고(서드파티 계산기): https://tools.devcomma.com/calculators/neis-word-counter , https://morningwalkai.com/neis-byte-calculator
