/**
 * Document Organizer - Main Script (Node.js)
 * 공문서를 공문 번호별로 자동 정리
 *
 * 사용법:
 *   node organize.mjs [config_path] [profile_name]   — 정리 실행
 *   node organize.mjs --undo [config_path]            — 마지막 정리 되돌리기
 * config_path 생략 시 기본 위치: ~/.claude/skills/document-organizer/config.json
 * 되돌리기 기록(.last-organize.json)은 config.json과 같은 폴더에 저장된다.
 */

import { readdirSync, mkdirSync, renameSync, rmdirSync, statSync, existsSync, readFileSync, writeFileSync, unlinkSync } from 'fs';
import { join, extname, dirname } from 'path';
import { homedir } from 'os';

// ── Config ──────────────────────────────────────────────
const SKILL_DIR = join(homedir(), '.claude', 'skills', 'document-organizer');

const args = process.argv.slice(2);
const flags = new Set(args.filter(a => a.startsWith('--')));
const positional = args.filter(a => !a.startsWith('--'));

const isUndo = flags.has('--undo');
const CONFIG_PATH = positional[0] || join(SKILL_DIR, 'config.json');
const PROFILE_NAME = (!isUndo && positional[1]) || null;
const UNDO_LOG_PATH = join(dirname(CONFIG_PATH), '.last-organize.json');

function loadConfig() {
  if (!existsSync(CONFIG_PATH)) return null;
  return JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'));
}

function getDirectories(config, profileName) {
  const name = profileName || config.default_profile || 'work';
  const profile = config.profiles?.[name];
  if (!profile) throw new Error(`프로필 '${name}'을 찾을 수 없습니다.`);
  return {
    scanPath: profile.path,
    destPath: profile.destination || profile.path
  };
}

// ── Pattern ─────────────────────────────────────────────
const PATTERN = /\(([^-]+)-(\d+)\s+\((본문|첨부)\)[^)]*\)/;

function groupFiles(files) {
  const groups = {};
  const folderNames = {};
  const unmatched = [];

  for (const name of files) {
    const m = name.match(PATTERN);
    if (m) {
      const key = `${m[1]}-${m[2]}`;
      (groups[key] ??= []).push(name);
      if (m[3] === '본문') {
        folderNames[key] = name.replace(extname(name), '');
      }
    } else {
      unmatched.push(name);
    }
  }
  return { groups, folderNames, unmatched };
}

// ── Organize ────────────────────────────────────────────
function organize(scanPath, destPath, groups, folderNames) {
  let movedCount = 0;
  let folderCount = 0;
  const moves = [];       // 되돌리기 기록용
  const createdDirs = [];
  const skipped = [];     // 같은 이름의 파일이 이미 있어 옮기지 않은 파일

  if (!existsSync(destPath)) {
    mkdirSync(destPath, { recursive: true });
    createdDirs.push(destPath);
  }

  for (const [key, fileNames] of Object.entries(groups)) {
    const fname = folderNames[key] || `공문_${key}`;
    const folderPath = join(destPath, fname);

    if (!existsSync(folderPath)) {
      mkdirSync(folderPath, { recursive: true });
      createdDirs.push(folderPath);
      folderCount++;
    }

    for (const fileName of fileNames) {
      const src = join(scanPath, fileName);
      const dst = join(folderPath, fileName);
      if (existsSync(src) && !existsSync(dst)) {
        renameSync(src, dst);
        moves.push({ from: src, to: dst });
        movedCount++;
      } else if (existsSync(src) && existsSync(dst)) {
        skipped.push({ file: fileName, docKey: key });
      }
    }
  }

  // 되돌리기 기록 저장
  const undoLog = {
    timestamp: new Date().toISOString(),
    moves,
    createdDirs
  };
  try {
    writeFileSync(UNDO_LOG_PATH, JSON.stringify(undoLog, null, 2), 'utf-8');
  } catch (e) {
    console.error(`경고: 되돌리기 기록을 저장하지 못했습니다 (${UNDO_LOG_PATH}): ${e.message}`);
  }

  return { folderCount, movedCount, skipped };
}

// ── Undo ────────────────────────────────────────────────
function undo() {
  let log = null;
  if (existsSync(UNDO_LOG_PATH)) {
    try { log = JSON.parse(readFileSync(UNDO_LOG_PATH, 'utf-8')); } catch { log = null; }
  }
  if (!log || !Array.isArray(log.moves)) {
    console.error('ERROR: 되돌릴 정리 기록이 없습니다.');
    process.exit(1);
  }

  console.log(`되돌리기: ${log.timestamp} 작업 (${log.moves.length}개 파일)`);

  let restored = 0;
  let errors = 0;

  // 파일을 원래 위치로 복원 (역순)
  for (const { from, to } of [...log.moves].reverse()) {
    if (!existsSync(to)) {
      console.log(`  건너뜀 (정리된 위치에 파일 없음): ${to}`);
      continue;
    }
    if (existsSync(from)) {
      console.log(`  건너뜀 (원래 위치에 같은 이름의 파일이 있음): ${from}`);
      continue;
    }
    try {
      renameSync(to, from);
      restored++;
    } catch (e) {
      console.error(`  실패: ${to} → ${e.message}`);
      errors++;
    }
  }

  // 정리할 때 새로 만든 폴더 중 비어 있는 폴더만 삭제 (역순)
  for (const dir of [...(log.createdDirs || [])].reverse()) {
    try {
      if (existsSync(dir) && readdirSync(dir).length === 0) {
        rmdirSync(dir);
        console.log(`  폴더 삭제: ${dir}`);
      }
    } catch { /* 비어 있지 않으면 그대로 둔다 */ }
  }

  // 한 번 되돌린 기록은 지운다
  try { unlinkSync(UNDO_LOG_PATH); } catch {}

  console.log(`\n복원: ${restored}개 파일`);
  if (errors) console.log(`실패: ${errors}개`);
}

// ── Main ────────────────────────────────────────────────
function main() {
  if (isUndo) {
    undo();
    return;
  }

  const config = loadConfig();
  if (!config) {
    console.error('ERROR: config.json을 찾을 수 없습니다.');
    process.exit(1);
  }

  const { scanPath, destPath } = getDirectories(config, PROFILE_NAME);
  if (!existsSync(scanPath)) {
    console.error(`ERROR: 경로가 존재하지 않습니다: ${scanPath}`);
    process.exit(1);
  }

  console.log(`스캔: ${scanPath}`);
  if (destPath !== scanPath) console.log(`정리: ${destPath}`);

  const allFiles = readdirSync(scanPath).filter(n => {
    try { return statSync(join(scanPath, n)).isFile(); } catch { return false; }
  });

  console.log(`총 파일: ${allFiles.length}개`);

  const { groups, folderNames, unmatched } = groupFiles(allFiles);
  const groupCount = Object.keys(groups).length;
  console.log(`공문 그룹: ${groupCount}개`);

  if (unmatched.length) {
    console.log(`패턴 미매칭: ${unmatched.length}개`);
    unmatched.forEach(f => console.log(`  - ${f}`));
  }

  if (groupCount === 0) {
    console.log('정리할 공문이 없습니다.');
    process.exit(0);
  }

  const { folderCount, movedCount, skipped } = organize(scanPath, destPath, groups, folderNames);

  console.log(`\n생성된 폴더: ${folderCount}개`);
  console.log(`이동된 파일: ${movedCount}개`);

  if (skipped.length) {
    // 공문번호별로 묶어서 보고
    const byDoc = {};
    for (const { file, docKey } of skipped) {
      (byDoc[docKey] ??= []).push(file);
    }
    console.log(`\n옮기지 않음 (정리 폴더에 같은 이름의 파일이 이미 있음): ${skipped.length}개`);
    for (const [docKey, files] of Object.entries(byDoc)) {
      console.log(`  [${docKey}] ${files.length}개 파일`);
      files.forEach(f => console.log(`    - ${f}`));
    }
  }
}

main();
