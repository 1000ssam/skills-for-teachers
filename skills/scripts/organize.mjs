/**
 * Document Organizer - Main Script (Node.js)
 * 공문서를 공문 번호별로 자동 정리
 *
 * 사용법: node organize.mjs [config_path]
 * config_path 생략 시 기본 위치: ~/.claude/skills/document-organizer/config.json
 */

import { readdirSync, mkdirSync, renameSync, statSync, existsSync, readFileSync } from 'fs';
import { join, extname } from 'path';
import { homedir } from 'os';

// ── Config ──────────────────────────────────────────────
const SKILL_DIR = join(homedir(), '.claude', 'skills', 'document-organizer');
const CONFIG_PATH = process.argv[2] || join(SKILL_DIR, 'config.json');
const PROFILE_NAME = process.argv[3] || null;

function loadConfig() {
  if (!existsSync(CONFIG_PATH)) return null;
  return JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'));
}

function getTargetDirectory(config, profileName) {
  const name = profileName || config.default_profile || 'work';
  const profile = config.profiles?.[name];
  if (!profile) throw new Error(`프로필 '${name}'을 찾을 수 없습니다.`);
  return profile.path;
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
function organize(basePath, groups, folderNames) {
  let movedCount = 0;
  let folderCount = 0;

  for (const [key, fileNames] of Object.entries(groups)) {
    const fname = folderNames[key] || `공문_${key}`;
    const folderPath = join(basePath, fname);

    if (!existsSync(folderPath)) {
      mkdirSync(folderPath, { recursive: true });
      folderCount++;
    }

    for (const fileName of fileNames) {
      const src = join(basePath, fileName);
      const dst = join(folderPath, fileName);
      if (existsSync(src) && !existsSync(dst)) {
        renameSync(src, dst);
        movedCount++;
      }
    }
  }
  return { folderCount, movedCount };
}

// ── Main ────────────────────────────────────────────────
function main() {
  const config = loadConfig();
  if (!config) {
    console.error('ERROR: config.json을 찾을 수 없습니다.');
    process.exit(1);
  }

  const basePath = getTargetDirectory(config, PROFILE_NAME);
  if (!existsSync(basePath)) {
    console.error(`ERROR: 경로가 존재하지 않습니다: ${basePath}`);
    process.exit(1);
  }

  const allFiles = readdirSync(basePath).filter(n => {
    try { return statSync(join(basePath, n)).isFile(); } catch { return false; }
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

  const { folderCount, movedCount } = organize(basePath, groups, folderNames);

  console.log(`\n생성된 폴더: ${folderCount}개`);
  console.log(`이동된 파일: ${movedCount}개`);
}

main();
