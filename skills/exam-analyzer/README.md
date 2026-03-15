# 📊 exam-analyzer (수능 기출 분석기)

교과서 단원 PDF와 수능/모평/학평 기출 PDF를 매칭하여 **기출 분석표**와 **문항별 스크린샷**을 자동 생성하는 Claude Code 스킬입니다.

## 대응 과목

모든 수능 과목에 대응합니다:
- 사회탐구 (한국사, 동아시아사, 세계사, 생활과윤리, 사회문화 등)
- 과학탐구 (물리학, 화학, 생명과학, 지구과학)
- 국어, 수학, 영어

## 설치

PowerShell에서 실행:

```powershell
irm https://raw.githubusercontent.com/1000ssam/skiils-for-teachers/main/skills/exam-analyzer/install.ps1 | iex
```

### 필요 환경
- [Claude Code](https://claude.ai/claude-code)
- Python 3.10+
- Python 패키지: `pymupdf`, `pillow`, `numpy` (설치 스크립트가 자동 설치)

## 사용법

Claude Code에서:

```
기출 분석 03
기출 분석 미적분
기출 분석 전자기 유도 p1-3
```

### 첫 실행 시

교과서 PDF 폴더와 기출 PDF 폴더 경로를 물어봅니다. 한 번 설정하면 이후 자동으로 기억합니다.

## 출력물

1. **기출 분석표** (`[단원번호]_[단원명]_기출분석.md`)
   - 시험별 출제 현황
   - 출제 패턴 분석
   - 키워드별 핵심 정리
   - 시험장 판별 체크리스트
   - 출제 경향 요약

2. **문항 스크린샷** (`[단원번호]_기출_스크린샷/`)
   - 관련 문항을 PDF에서 개별 크롭한 WebP 이미지
   - 과목 라벨·페이지 번호 자동 제거
   - 사방 균일 패딩 적용

## 기출 PDF 준비

EBSi(ebsi.co.kr) 등에서 기출 PDF를 다운로드하여 한 폴더에 모아두세요. 파일명은 상관없으며, 시험 유형은 PDF 내용에서 자동 식별합니다.
