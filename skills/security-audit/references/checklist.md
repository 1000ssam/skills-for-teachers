# Security Checklist by App Type

## 웹앱 (풀스택) — Next.js, Nuxt, Remix 등

### 필수 (Must Have)

| # | 항목 | 설명 | 확인 방법 |
|---|------|------|----------|
| W1 | **Input Validation** | 모든 사용자 입력에 Zod/Joi 스키마 적용, HTML 태그 스트립 | API 라우트에서 `req.json()` 직후 검증 존재 여부 |
| W2 | **RBAC + AuthN/AuthZ** | 모든 API 라우트에 인증 가드, 역할 기반 접근 제어 | `auth()` 또는 `getServerSession()` 호출 존재 여부 |
| W3 | **Tenant Isolation** | 리소스 소유자 검증 (A 사용자가 B의 데이터 접근 불가) | `where` 절에 `userId` 또는 `createdBy` 포함 여부 |
| W4 | **Cross-entity 검증** | 관계된 ID가 해당 리소스에 속하는지 검증 | 예: questionId가 해당 examId에 속하는지 |
| W5 | **에러 노출 차단** | 에러 응답에 스택 트레이스, DB 경로 등 미포함 | catch 블록에서 generic 메시지 반환 여부 |
| W6 | **Security Headers** | CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff | 미들웨어 또는 next.config 헤더 설정 |
| W7 | **Cookie 보안** | HttpOnly, Secure, SameSite=Lax 이상 | auth 설정 파일 확인 |
| W8 | **Rate Limiting** | 인증/제출 등 민감 엔드포인트에 요청 제한 | 미들웨어 또는 라우트별 제한 로직 |
| W9 | **Secret 관리** | 환경 변수 사용, 하드코딩 금지, .env가 .gitignore에 포함 | grep으로 하드코딩된 키 검색 |

### 권장 (Nice to Have)

| # | 항목 | 설명 |
|---|------|------|
| W10 | CSRF 방어 | Origin 헤더 검증 (NextAuth 등이 자체 처리하면 이중 방어) |
| W11 | CORS 제한 | 외부 API 공개 시 필요, Same-origin만이면 우선순위 낮음 |
| W12 | HSTS | Vercel/Cloudflare 등 플랫폼이 자동 적용하면 불필요 |
| W13 | Audit Logging | MVP에선 console.log JSON, 프로덕션에서 외부 서비스 |
| W14 | 세션 만료 설정 | 앱 특성에 맞는 maxAge (시험 앱: 짧게, 일반 앱: 길게) |
| W15 | 의존성 점검 | `npm audit` — dev-only 취약점은 무시 가능 |

### 해당 없음 (자동 제외)

| 조건 | 제외 항목 | 이유 |
|------|----------|------|
| Prisma/Drizzle 등 ORM 사용 | SQLi 방어 | ORM이 파라미터 바인딩 처리 |
| 서버가 사용자 URL을 fetch 안 함 | SSRF | 공격 벡터 없음 |
| 정적 사이트 (API 없음) | RBAC, Rate Limit, CSRF | 서버 로직 없음 |

---

## API 서버 (Express, Fastify, Hono 등)

웹앱과 동일하되 다음 추가:

| # | 항목 | 설명 |
|---|------|------|
| A1 | **CORS 설정** | 허용 출처 명시적 화이트리스트 (와일드카드 금지) |
| A2 | **API 키 인증** | 공개 API면 API 키 + 사용량 제한 |
| A3 | **요청 크기 제한** | body-parser limit 설정 (기본 100kb 등) |

---

## 일렉트론 앱

### 필수

| # | 항목 | 설명 |
|---|------|------|
| E1 | **nodeIntegration: false** | 렌더러에서 Node.js API 접근 차단 |
| E2 | **contextIsolation: true** | 프리로드 스크립트와 웹 콘텐츠 격리 |
| E3 | **remote 모듈 비활성화** | `enableRemoteModule: false` |
| E4 | **webSecurity 유지** | `webSecurity: false` 설정 금지 |
| E5 | **프로토콜 핸들러 검증** | 커스텀 프로토콜 URL 검증 |
| E6 | **외부 URL 네비게이션 차단** | `will-navigate` 이벤트에서 화이트리스트 검증 |
| E7 | **자동 업데이트 서명 검증** | electron-updater 코드 서명 |
| E8 | **로컬 DB 암호화** | SQLCipher 또는 유사 솔루션 |
| E9 | **Input Validation** | 웹앱과 동일 |
| E10 | **에러 노출 차단** | 웹앱과 동일 |

### 웹앱 항목 중 해당 없음

| 제외 항목 | 이유 |
|----------|------|
| CSRF | 브라우저 쿠키 자동 첨부 환경 아님 |
| CORS | 로컬 앱, 외부 출처 요청 없음 |
| Cookie 보안 | 쿠키 기반 세션 미사용 |
| HSTS | 네트워크 구조 다름 |
| Rate Limiting | 로컬 앱이면 의미 없음 |

---

## 정적 사이트

### 필수

| # | 항목 | 설명 |
|---|------|------|
| S1 | **CSP 헤더** | 외부 스크립트 삽입 방어 |
| S2 | **Subresource Integrity** | CDN 스크립트에 integrity 속성 |
| S3 | **Secret 미포함** | 클라이언트 코드에 API 키 하드코딩 금지 |

나머지 서버 관련 항목은 해당 없음.
