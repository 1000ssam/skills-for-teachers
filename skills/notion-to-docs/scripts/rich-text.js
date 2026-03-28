/**
 * Rich Text Parser — Notion 마크다운 인라인 서식 → 세그먼트 배열
 *
 * Notion의 <span> 태그(underline, color)와 표준 마크다운 인라인 서식을 파싱한다.
 * \x01/\x02 마커를 사용해 <span>을 먼저 치환 → 표준 마크다운 파싱의 2단계 접근.
 */

/**
 * Notion 마크다운의 인라인 서식 파싱
 * @param {string} text
 * @returns {Array<{ text: string, styles: object, link?: string }>}
 */
export function parseInlineMarkdown(text) {
  if (!text) return [{ text: '', styles: {} }];

  // 1단계: <span> 태그를 내부 마커로 변환
  let processed = text;
  processed = processed.replace(/<span\s+underline="true">(.*?)<\/span>/g, (_, inner) => `\x01U${inner}\x01u`);
  processed = processed.replace(/<span\s+color="([^"]+)">(.*?)<\/span>/g, (_, color, inner) => `\x01C${color}\x02${inner}\x01c`);

  // 2단계: 마크다운 이스케이프 해제 (\* → *, \_ → _ 등)
  processed = processed.replace(/\\([*_~`\\\[\]<>#\-()!|])/g, '$1');

  // 3단계: 표준 마크다운 + 마커 파싱
  return parseWithMarkers(processed);
}

function parseWithMarkers(text) {
  const segments = [];
  let i = 0;
  let buffer = '';

  function flush() {
    if (buffer.length > 0) {
      segments.push({ text: buffer, styles: {} });
      buffer = '';
    }
  }

  while (i < text.length) {
    // ── 밑줄 마커 ──
    if (text.slice(i, i + 2) === '\x01U') {
      flush();
      const end = text.indexOf('\x01u', i + 2);
      if (end > i) {
        const innerSegs = parseWithMarkers(text.slice(i + 2, end));
        for (const seg of innerSegs) { seg.styles.underline = true; segments.push(seg); }
        i = end + 2;
        continue;
      }
    }

    // ── 색상 마커 ──
    if (text.slice(i, i + 2) === '\x01C') {
      flush();
      const colorEnd = text.indexOf('\x02', i + 2);
      if (colorEnd > i) {
        const color = text.slice(i + 2, colorEnd);
        const end = text.indexOf('\x01c', colorEnd + 1);
        if (end > colorEnd) {
          const innerSegs = parseWithMarkers(text.slice(colorEnd + 1, end));
          for (const seg of innerSegs) { seg.styles.color = color; segments.push(seg); }
          i = end + 2;
          continue;
        }
      }
    }

    // ── 링크: [text](url) ──
    if (text[i] === '[') {
      const closeBracket = text.indexOf(']', i);
      if (closeBracket > i && text[closeBracket + 1] === '(') {
        const closeParen = text.indexOf(')', closeBracket + 2);
        if (closeParen > closeBracket) {
          flush();
          segments.push({ text: text.slice(i + 1, closeBracket), styles: { link: true }, link: text.slice(closeBracket + 2, closeParen) });
          i = closeParen + 1;
          continue;
        }
      }
    }

    // ── 볼드+이탤릭: ***text*** ──
    if (text.slice(i, i + 3) === '***') {
      const end = text.indexOf('***', i + 3);
      if (end > i) { flush(); segments.push({ text: text.slice(i + 3, end), styles: { bold: true, italic: true } }); i = end + 3; continue; }
    }

    // ── 볼드: **text** ──
    if (text.slice(i, i + 2) === '**') {
      const end = text.indexOf('**', i + 2);
      if (end > i) { flush(); segments.push({ text: text.slice(i + 2, end), styles: { bold: true } }); i = end + 2; continue; }
    }

    // ── 취소선: ~~text~~ ──
    if (text.slice(i, i + 2) === '~~') {
      const end = text.indexOf('~~', i + 2);
      if (end > i) { flush(); segments.push({ text: text.slice(i + 2, end), styles: { strikethrough: true } }); i = end + 2; continue; }
    }

    // ── 이탤릭: *text* ──
    if (text[i] === '*' && text[i + 1] !== '*') {
      const end = text.indexOf('*', i + 1);
      if (end > i && text[end + 1] !== '*') { flush(); segments.push({ text: text.slice(i + 1, end), styles: { italic: true } }); i = end + 1; continue; }
    }

    // ── 인라인 코드: `text` ──
    if (text[i] === '`') {
      const end = text.indexOf('`', i + 1);
      if (end > i) { flush(); segments.push({ text: text.slice(i + 1, end), styles: { code: true } }); i = end + 1; continue; }
    }

    // ── 인라인 수식: $`expr`$ ──
    if (text.slice(i, i + 2) === '$`') {
      const end = text.indexOf('`$', i + 2);
      if (end > i) { flush(); segments.push({ text: text.slice(i + 2, end), styles: { italic: true } }); i = end + 2; continue; }
    }

    buffer += text[i];
    i++;
  }

  flush();
  return segments.filter(s => s.text.length > 0);
}
