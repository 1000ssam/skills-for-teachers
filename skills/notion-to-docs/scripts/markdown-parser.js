/**
 * Markdown Parser — Notion 확장 마크다운 → 구조화된 블록 배열
 *
 * Notion getPageMarkdown() 실제 반환 형식:
 * - 들여쓰기: 탭(\t), 헤딩 토글의 자식도 탭으로 들여쓰기
 * - 헤딩 토글: `# 제목 {toggle="true"}` → 자식은 탭 들여쓰기
 * - <callout>, <details>, <table>, <unknown>, <database>, <empty-block/>
 * - <span underline="true">, <span color="...">, <br>
 * - 이미지: ![alt](url)
 */

import { parseInlineMarkdown } from './rich-text.js';

/**
 * 전처리: <br> → \n, <empty-block/> 제거
 */
function preprocess(markdown) {
  return markdown
    .replace(/<br\s*\/?>/g, ' ')
    .replace(/^[\t]*<empty-block\/>$/gm, '');
}

/**
 * 헤딩에서 {toggle="true" ...} 속성 제거
 */
function stripToggleAttr(content) {
  return content.replace(/\s*\{toggle="true"(?:\s+color="[^"]*")?\}\s*$/, '').trim();
}

export function parseNotionMarkdown(markdown, supplementBlocks = []) {
  const lines = preprocess(markdown).split('\n');
  const blocks = [];
  let i = 0;
  let unknownIndex = 0;

  const unknownSupplements = supplementBlocks.filter(b =>
    ['bookmark', 'embed', 'image', 'video', 'file', 'pdf', 'link_preview'].includes(b.type)
  );

  while (i < lines.length) {
    const line = lines[i];
    const stripped = line.replace(/^\t+/, '');
    const tabCount = line.length - stripped.length;
    const trimmed = stripped.trim();

    if (trimmed === '') { i++; continue; }

    // ── 코드 블록 ──
    if (trimmed.startsWith('```')) {
      const lang = trimmed.slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trimStart().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++;
      blocks.push({ type: 'code', content: codeLines.join('\n'), segments: [], depth: tabCount, meta: { language: lang || 'plain text' } });
      continue;
    }

    // ── 수식 블록 ──
    if (trimmed.startsWith('$$')) {
      i++;
      const eqLines = [];
      while (i < lines.length && !lines[i].trimStart().startsWith('$$')) {
        eqLines.push(lines[i].trim());
        i++;
      }
      if (i < lines.length) i++;
      const expr = eqLines.join('\n').trim();
      blocks.push({ type: 'equation', content: expr, segments: [{ text: expr, styles: {} }], depth: tabCount, meta: {} });
      continue;
    }

    // ── <table_of_contents/> ──
    if (trimmed === '<table_of_contents/>') {
      blocks.push({ type: 'table_of_contents', content: '[목차]', segments: [{ text: '[목차]', styles: {} }], depth: 0, meta: {} });
      i++; continue;
    }

    // ── <empty-block/> (전처리에서 빈 줄이 되지만 혹시 남은 것) ──
    if (trimmed === '<empty-block/>') { i++; continue; }

    // ── <unknown> ──
    const unknownMatch = trimmed.match(/^<unknown\s+(?:url="([^"]*)")?\s*(?:alt="([^"]*)")?\s*\/?\s*>/);
    if (unknownMatch) {
      const altType = unknownMatch[2] || 'unknown';
      const url = unknownMatch[1] || '';
      const supplement = unknownSupplements[unknownIndex] || null;
      unknownIndex++;

      if (supplement) {
        const block = convertSupplementBlock(supplement, tabCount);
        if (block) blocks.push(block);
      } else if (url && altType === 'bookmark') {
        blocks.push({ type: 'bookmark', content: url, segments: [{ text: url, styles: { link: true }, link: url }], depth: tabCount, meta: { url } });
      }
      // alias 등 변환 불가 블록은 무시
      i++; continue;
    }

    // ── <callout> ──
    const calloutMatch = trimmed.match(/^<callout(?:\s+icon="([^"]*)")?(?:\s+color="([^"]*)")?\s*>/);
    if (calloutMatch) {
      const icon = calloutMatch[1] || '';
      const color = calloutMatch[2] || 'default';
      const normalizedColor = color.endsWith('_bg') ? color.replace('_bg', '_background') : color;

      // 콜아웃 내부 라인 수집
      i++;
      const innerLines = [];
      while (i < lines.length && !lines[i].includes('</callout>')) {
        innerLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++;

      // 내부에 마크다운 구조(헤딩, 리스트 등)가 있으면 재귀 파싱
      const innerText = innerLines.join('\n').trim();
      const hasStructure = innerLines.some(l => {
        const t = l.replace(/^\t+/, '').trim();
        return t.startsWith('#') || t.startsWith('- ') || t.startsWith('* ') || t.match(/^\d+\.\s/) || t.startsWith('> ');
      });

      if (hasStructure) {
        const innerBlocks = parseNotionMarkdown(innerLines.join('\n'), []);
        const minDepth = Math.min(...innerBlocks.map(b => b.depth));
        for (let bi = 0; bi < innerBlocks.length; bi++) {
          const ib = innerBlocks[bi];
          // 콜아웃 내부는 상대 depth만 유지 (최소 0)
          ib.depth = Math.max(0, ib.depth - minDepth);
          if (bi === 0 && icon) {
            ib.content = `${icon} ${ib.content}`;
            ib.segments = parseInlineMarkdown(ib.content);
          }
          ib.meta = { ...ib.meta, calloutColor: normalizedColor, calloutIcon: icon };
          // 첫/마지막 블록 표시 (콜아웃 여백용)
          if (bi === 0) ib.meta.calloutFirst = true;
          if (bi === innerBlocks.length - 1) ib.meta.calloutLast = true;
          blocks.push(ib);
        }
      } else {
        // 단순 텍스트 콜아웃 — 탭 제거 후 합치기
        const cleanedContent = innerLines.map(l => l.replace(/^\t+/, '').trim()).filter(l => l).join('\n');
        const displayContent = icon ? `${icon} ${cleanedContent}` : cleanedContent;
        blocks.push({
          type: 'callout', content: displayContent,
          segments: parseInlineMarkdown(displayContent),
          depth: tabCount, meta: { icon, color: normalizedColor },
        });
      }
      continue;
    }

    // ── <details> (일반 토글 — 자식은 탭 들여쓰기로 이미 표현됨) ──
    if (trimmed.startsWith('<details>')) {
      let summaryLine = trimmed;
      if (!summaryLine.includes('<summary>')) {
        i++;
        if (i < lines.length) summaryLine = lines[i].trim();
      }
      const summaryMatch = summaryLine.match(/<summary>(.*?)<\/summary>/);
      const title = summaryMatch ? summaryMatch[1].trim() : '토글';

      blocks.push({
        type: 'toggle', content: `\u25B8 ${title}`,
        segments: parseInlineMarkdown(`\u25B8 ${title}`),
        depth: tabCount, meta: {},
      });

      // <details> 내부 라인은 건너뛰고 </details>까지 스킵
      // 자식 블록은 탭 들여쓰기로 이미 표현되어 있어 메인 루프에서 처리됨
      // ...하지만 실제로는 <details> 안에 라인이 있으므로 수집 후 재파싱
      i++;
      const innerLines = [];
      while (i < lines.length && !lines[i].trimStart().startsWith('</details>')) {
        innerLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++; // skip </details>

      // 내부 라인을 메인 파서로 재파싱 (depth는 탭에서 자동 결정)
      if (innerLines.length > 0) {
        const innerBlocks = parseNotionMarkdown(innerLines.join('\n'), []);
        blocks.push(...innerBlocks);
      }
      continue;
    }

    // ── <columns> → 내부 컬럼을 순차 렌더링 ──
    if (trimmed === '<columns>') {
      i++;
      const innerLines = [];
      while (i < lines.length && lines[i].trim() !== '</columns>') {
        const cl = lines[i].trim();
        // <column>, </column> 태그는 건너뛰고 내부 콘텐츠만 수집
        if (cl !== '<column>' && cl !== '</column>') {
          innerLines.push(lines[i]);
        }
        i++;
      }
      if (i < lines.length) i++; // skip </columns>
      if (innerLines.length > 0) {
        const innerBlocks = parseNotionMarkdown(innerLines.join('\n'), []);
        blocks.push(...innerBlocks);
      }
      continue;
    }

    // ── <table> ──
    if (trimmed.startsWith('<table')) {
      i++;
      const rows = [];
      while (i < lines.length && !lines[i].trim().startsWith('</table>')) {
        const rowLine = lines[i].trim();
        if (rowLine === '<tr>') {
          const cells = [];
          i++;
          while (i < lines.length && lines[i].trim() !== '</tr>') {
            const cellMatch = lines[i].trim().match(/^<td>(.*?)<\/td>$/);
            if (cellMatch) cells.push(cellMatch[1]);
            i++;
          }
          rows.push(cells);
        }
        i++;
      }
      if (i < lines.length) i++;
      blocks.push({ type: 'table', content: '', segments: [], depth: tabCount, meta: { rows, rowCount: rows.length, colCount: rows[0]?.length || 0 } });
      continue;
    }

    // ── 이미지 ──
    const imgMatch = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imgMatch) {
      blocks.push({ type: 'image', content: imgMatch[1] || '', segments: [], depth: tabCount, meta: { url: imgMatch[2], caption: imgMatch[1] } });
      i++; continue;
    }

    // ── 구분선 ──
    if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
      blocks.push({ type: 'divider', content: '———', segments: [{ text: '———', styles: {} }], depth: 0, meta: {} });
      i++; continue;
    }

    // ── Heading (토글 속성 제거 포함) ──
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const rawContent = headingMatch[2];
      const content = stripToggleAttr(rawContent);
      blocks.push({
        type: `heading_${level}`, content,
        segments: parseInlineMarkdown(content),
        depth: tabCount, meta: {},
      });
      i++; continue;
    }

    // ── 인용 ──
    if (trimmed.startsWith('> ')) {
      const quoteLines = [];
      while (i < lines.length && lines[i].replace(/^\t+/, '').trim().startsWith('> ')) {
        quoteLines.push(lines[i].replace(/^\t+/, '').trim().slice(2));
        i++;
      }
      const content = quoteLines.join('\n');
      blocks.push({ type: 'quote', content, segments: parseInlineMarkdown(content), depth: tabCount, meta: {} });
      continue;
    }

    // ── 체크리스트 ──
    const todoMatch = trimmed.match(/^-\s+\[([ xX])\]\s+(.*)/);
    if (todoMatch) {
      const checked = todoMatch[1] !== ' ';
      const prefix = checked ? '\u2611 ' : '\u2610 ';
      const content = prefix + todoMatch[2];
      blocks.push({ type: 'to_do', content, segments: parseInlineMarkdown(content), depth: tabCount, meta: { checked } });
      i++; continue;
    }

    // ── 불릿 리스트 (** 볼드 시작 제외) ──
    if (trimmed.match(/^[-*]\s+(.+)/) && !trimmed.startsWith('**')) {
      const content = trimmed.replace(/^[-*]\s+/, '');
      blocks.push({ type: 'bulleted_list_item', content, segments: parseInlineMarkdown(content), depth: tabCount, meta: {} });
      i++; continue;
    }

    // ── 넘버드 리스트 (** 볼드 감싸기 내부 제외) ──
    const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
    if (numberedMatch && !trimmed.startsWith('**')) {
      blocks.push({ type: 'numbered_list_item', content: numberedMatch[2], segments: parseInlineMarkdown(numberedMatch[2]), depth: tabCount, meta: { number: parseInt(numberedMatch[1]) } });
      i++; continue;
    }

    // ── <database> → 무시 ──
    if (trimmed.startsWith('<database')) {
      while (i < lines.length && !lines[i].includes('</database>') && !lines[i].includes('/>')) i++;
      i++;
      continue;
    }

    // ── 일반 단락 ──
    blocks.push({ type: 'paragraph', content: trimmed, segments: parseInlineMarkdown(trimmed), depth: tabCount, meta: {} });
    i++;
  }

  return blocks;
}

function convertSupplementBlock(block, depth) {
  switch (block.type) {
    case 'bookmark': {
      const url = block.bookmark?.url || '';
      const caption = block.bookmark?.caption?.[0]?.plain_text || url;
      return { type: 'bookmark', content: caption, segments: [{ text: caption, styles: { link: true }, link: url }], depth, meta: { url } };
    }
    case 'image': {
      const url = block.image?.file?.url || block.image?.external?.url || '';
      return { type: 'image', content: '', segments: [], depth, meta: { url, caption: block.image?.caption?.[0]?.plain_text || '' } };
    }
    case 'embed': {
      const url = block.embed?.url || '';
      return { type: 'fallback', content: `[임베드: ${url}]`, segments: [{ text: `[임베드: ${url}]`, styles: { link: true }, link: url }], depth, meta: { originalType: 'embed', url } };
    }
    case 'video': {
      const url = block.video?.external?.url || block.video?.file?.url || '';
      return { type: 'fallback', content: `[동영상: ${url}]`, segments: [{ text: `[동영상: ${url}]`, styles: { link: true }, link: url }], depth, meta: { originalType: 'video', url } };
    }
    case 'file':
    case 'pdf': {
      const fd = block[block.type];
      const url = fd?.file?.url || fd?.external?.url || '';
      return { type: 'fallback', content: `[${block.type}: ${url}]`, segments: [{ text: `[${block.type}]`, styles: { link: true }, link: url }], depth, meta: { originalType: block.type, url } };
    }
    case 'link_preview': {
      const url = block.link_preview?.url || '';
      return { type: 'bookmark', content: url, segments: [{ text: url, styles: { link: true }, link: url }], depth, meta: { url } };
    }
    default: return null;
  }
}
