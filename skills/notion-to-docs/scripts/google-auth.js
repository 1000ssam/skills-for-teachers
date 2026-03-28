/**
 * Google OAuth2 인증 모듈 — 스킬 배포용
 *
 * 스킬 디렉토리 내 google-client.json + token.json으로 인증.
 * 토큰 만료 시 refresh_token으로 자동 갱신.
 * 최초 인증 시 브라우저 기반 OAuth flow 실행.
 */

import { readFileSync, writeFileSync } from 'fs';
import { createServer } from 'http';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLIENT_SECRET_PATH = join(__dirname, 'google-client.json');
const TOKEN_PATH = join(__dirname, '..', 'token.json');
const SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.file'];

let cachedToken = null;
let cachedClientSecret = null;

function loadClientSecret() {
  if (!cachedClientSecret) {
    let raw;
    try {
      raw = JSON.parse(readFileSync(CLIENT_SECRET_PATH, 'utf-8'));
    } catch {
      throw new Error(
        `google-client.json을 찾을 수 없습니다: ${CLIENT_SECRET_PATH}\n` +
        '스킬 설치가 올바르게 되었는지 확인해 주세요.'
      );
    }
    cachedClientSecret = raw[Object.keys(raw)[0]];
  }
  return cachedClientSecret;
}

export async function getAccessToken() {
  if (cachedToken && cachedToken.expiry_date > Date.now() + 60000) {
    return cachedToken.access_token;
  }

  // 저장된 토큰 로드
  try {
    const token = JSON.parse(readFileSync(TOKEN_PATH, 'utf-8'));

    // 만료 전이면 바로 반환
    if (token.expiry_date > Date.now() + 60000) {
      cachedToken = token;
      return token.access_token;
    }

    // refresh_token으로 갱신
    if (token.refresh_token) {
      const refreshed = await refreshAccessToken(token.refresh_token);
      if (refreshed) {
        cachedToken = refreshed;
        return refreshed.access_token;
      }
    }
  } catch {
    // 토큰 파일 없거나 파싱 실패 — 새 인증 진행
  }

  // 새 인증 필요
  const token = await authorizeInteractive();
  cachedToken = token;
  return token.access_token;
}

async function refreshAccessToken(refreshToken) {
  const client = loadClientSecret();
  const params = new URLSearchParams({
    client_id: client.client_id,
    client_secret: client.client_secret,
    refresh_token: refreshToken,
    grant_type: 'refresh_token',
  });

  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });

  if (!res.ok) {
    console.error('토큰 갱신 실패:', await res.text());
    return null;
  }

  const data = await res.json();
  const token = {
    access_token: data.access_token,
    refresh_token: refreshToken,
    expiry_date: Date.now() + (data.expires_in * 1000),
  };
  writeFileSync(TOKEN_PATH, JSON.stringify(token, null, 2));
  return token;
}

async function authorizeInteractive() {
  const client = loadClientSecret();
  const PORT = 35556;
  const redirectUri = `http://localhost:${PORT}`;

  const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` + new URLSearchParams({
    client_id: client.client_id,
    redirect_uri: redirectUri,
    response_type: 'code',
    scope: SCOPES.join(' '),
    access_type: 'offline',
    prompt: 'consent',
  }).toString();

  console.log('\n=== Google 인증 필요 ===');
  console.log('아래 URL을 브라우저에서 열어주세요:\n');
  console.log(authUrl);
  console.log('\n인증 대기 중...\n');

  // 브라우저 자동 열기 시도 (WSL, macOS, Linux)
  try {
    const { execSync } = await import('child_process');
    const { platform } = await import('os');
    const os = platform();
    if (os === 'win32') {
      execSync(`start "${authUrl}"`, { stdio: 'ignore' });
    } else if (os === 'darwin') {
      execSync(`open "${authUrl}"`, { stdio: 'ignore' });
    } else {
      // WSL 또는 Linux
      try {
        execSync(`/mnt/c/Windows/explorer.exe "${authUrl}"`, { stdio: 'ignore' });
      } catch {
        execSync(`xdg-open "${authUrl}"`, { stdio: 'ignore' }).catch(() => {});
      }
    }
  } catch { /* ignore — user can open URL manually */ }

  // 콜백 서버
  const code = await new Promise((resolve, reject) => {
    const server = createServer((req, res) => {
      const url = new URL(req.url, `http://localhost:${PORT}`);
      const code = url.searchParams.get('code');
      if (code) {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end('<h1>인증 완료!</h1><p>이 탭을 닫아도 됩니다.</p>');
        server.close();
        resolve(code);
      } else {
        res.writeHead(400);
        res.end('No code parameter');
      }
    });
    server.listen(PORT);
    server.on('error', reject);
  });

  // 코드 → 토큰 교환
  const params = new URLSearchParams({
    code,
    client_id: client.client_id,
    client_secret: client.client_secret,
    redirect_uri: redirectUri,
    grant_type: 'authorization_code',
  });

  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });

  if (!res.ok) {
    throw new Error('토큰 교환 실패: ' + await res.text());
  }

  const data = await res.json();
  const token = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expiry_date: Date.now() + (data.expires_in * 1000),
  };
  writeFileSync(TOKEN_PATH, JSON.stringify(token, null, 2));
  console.log('Google 인증 완료, 토큰 저장됨');
  return token;
}

// --setup 플래그로 직접 실행 시 인증만 수행
if (process.argv.includes('--setup')) {
  getAccessToken()
    .then(() => console.log('Google 인증 설정 완료!'))
    .catch(err => { console.error('인증 실패:', err.message); process.exit(1); });
}
