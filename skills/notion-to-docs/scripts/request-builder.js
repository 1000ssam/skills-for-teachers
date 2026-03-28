/**
 * Request Builder — 구조화된 블록 → Google Docs batchUpdate 요청 배열
 *
 * 핵심 모듈. style-map.js에서 스타일을 읽고, 각 블록을 Google Docs API 요청으로 변환한다.
 * 인덱스 추적, 리치 텍스트 오버레이, 불릿 범위 수집, 테이블 2-pass 등을 처리한다.
 */

import { STYLES, NOTION_COLORS, NOTION_BG_COLORS, INDENT_PER_LEVEL } from './style-map.js';
import { parseInlineMarkdown } from './rich-text.js';

function buildParagraphFields(style) {
  return Object.keys(style).join(',');
}

function buildTextFields(style) {
  return Object.keys(style).join(',');
}

/**
 * 구조화된 블록 배열 → batchUpdate 요청 배열
 * @param {Array} blocks - markdown-parser.js의 출력
 * @returns {{ requests: Array }}
 */
export function buildRequests(blocks) {
  const requests = [];
  let insertIndex = 1;
  const bulletRanges = [];
  const pendingTables = []; // 후처리할 테이블 정보
  let lastHeadingDepth = 0;
  let numberedCounter = 0;

  for (const block of blocks) {
    const style = STYLES[block.type] || STYLES.fallback;

    // 헤딩은 항상 indent=0, 비헤딩은 부모 헤딩 기준 상대 indent
    const isHeading = block.type.startsWith('heading_');
    const isInsideCallout = !!block.meta?.calloutColor;
    if (isHeading && !isInsideCallout) {
      lastHeadingDepth = block.depth;
      block.depth = 0;
    } else if (isHeading && isInsideCallout) {
      block.depth = 0; // 콜아웃 내부 헤딩도 indent=0이지만 lastHeadingDepth는 업데이트 안 함
    } else {
      block.depth = Math.max(0, block.depth - lastHeadingDepth - 1);
    }

    // 콜아웃 내부 구조 블록에 배경색 + 그룹 여백 + 3칸 스페이스 적용
    let effectiveStyle = style;
    if (block.meta?.calloutColor && block.type !== 'callout') {
      effectiveStyle = buildCalloutStyle(style, block.meta.calloutColor);
      // 구조 콜아웃 첫 블록 앞에 빈 단락
      if (block.meta.calloutFirst) {
        insertIndex = insertSpacer(requests, insertIndex, STYLES.callout.groupSpaceAbove);
      }
      // 3칸 스페이스 접두사 (이모지 있는 콜아웃의 헤더는 제외 — 아이콘이 이미 접두사)
      const isIconHeader = block.meta.calloutFirst && block.meta.calloutIcon;
      if (!isIconHeader) {
        block.content = '   ' + (block.content || '');
        block.segments = parseInlineMarkdown(block.content);
      }
    }

    switch (block.type) {
      case 'heading_1':
      case 'heading_2':
      case 'heading_3':
      case 'heading_4':
      case 'paragraph':
      case 'to_do':
      case 'toggle':
      case 'quote':
      case 'equation':
      case 'table_of_contents':
      case 'fallback': {
        const result = insertTextBlock(requests, insertIndex, block, effectiveStyle);
        insertIndex = result.endIndex;
        break;
      }

      case 'callout': {
        // 콜아웃 앞 빈 단락 (여백용, 배경색 없음)
        insertIndex = insertSpacer(requests, insertIndex, STYLES.callout.groupSpaceAbove);

        const calloutStyle = buildCalloutStyle(style, block.meta.color);
        if (!block.meta.icon) {
          block.content = '   ' + (block.content || '');
          block.segments = parseInlineMarkdown(block.content);
        }
        const result = insertTextBlock(requests, insertIndex, block, calloutStyle);
        insertIndex = result.endIndex;
        break;
      }

      case 'bulleted_list_item': {
        if (block.meta?.calloutColor) {
          // 콜아웃 내부 불릿: 텍스트 접두사 (3칸 스페이스는 위에서 이미 적용됨)
          const bulletBlock = { ...block, content: `• ${block.content}`, segments: parseInlineMarkdown(`• ${block.content}`) };
          const result = insertTextBlock(requests, insertIndex, bulletBlock, effectiveStyle);
          insertIndex = result.endIndex;
        } else {
          const result = insertTextBlock(requests, insertIndex, block, effectiveStyle);
          bulletRanges.push({
            startIndex: result.startIndex,
            endIndex: result.endIndex,
            preset: style.bulletPreset,
            depth: block.depth,
            type: block.type,
          });
          insertIndex = result.endIndex;
        }
        break;
      }

      case 'numbered_list_item': {
        const num = block.meta?.number || ++numberedCounter;
        numberedCounter = num;
        const numberedContent = `${num}. ${block.content}`;
        const numberedBlock = { ...block, content: numberedContent, segments: parseInlineMarkdown(numberedContent) };
        const result = insertTextBlock(requests, insertIndex, numberedBlock, effectiveStyle);
        insertIndex = result.endIndex;
        break;
      }

      case 'code': {
        // 언어 라벨
        if (block.meta.language && block.meta.language !== 'plain text') {
          const labelStyle = STYLES.code_label;
          const labelText = block.meta.language + '\n';
          requests.push({ insertText: { location: { index: insertIndex }, text: labelText } });
          const labelStart = insertIndex;
          const labelEnd = insertIndex + labelText.length;
          applyParagraphStyle(requests, labelStart, labelEnd, labelStyle.paragraphStyle, block.depth);
          applyTextStyle(requests, labelStart, labelEnd - 1, labelStyle.textStyle);
          insertIndex = labelEnd;
        }

        // 코드 본문
        const codeText = block.content + '\n';
        requests.push({ insertText: { location: { index: insertIndex }, text: codeText } });
        const codeStart = insertIndex;
        const codeEnd = insertIndex + codeText.length;
        applyParagraphStyle(requests, codeStart, codeEnd, style.paragraphStyle, block.depth);
        applyTextStyle(requests, codeStart, codeEnd - 1, style.textStyle);
        insertIndex = codeEnd;
        break;
      }

      case 'divider': {
        const divText = '———\n';
        requests.push({ insertText: { location: { index: insertIndex }, text: divText } });
        const divStart = insertIndex;
        const divEnd = insertIndex + divText.length;
        applyParagraphStyle(requests, divStart, divEnd, style.paragraphStyle, 0);
        applyTextStyle(requests, divStart, divEnd - 1, style.textStyle);
        insertIndex = divEnd;
        break;
      }

      case 'bookmark': {
        const urlText = block.content + '\n';
        requests.push({ insertText: { location: { index: insertIndex }, text: urlText } });
        const bmStart = insertIndex;
        const bmEnd = insertIndex + urlText.length;
        applyParagraphStyle(requests, bmStart, bmEnd, style.paragraphStyle, block.depth);
        applyTextStyle(requests, bmStart, bmEnd - 1, style.textStyle);
        // 하이퍼링크
        if (block.meta.url) {
          requests.push({
            updateTextStyle: {
              range: { startIndex: bmStart, endIndex: bmEnd - 1 },
              textStyle: { link: { url: block.meta.url } },
              fields: 'link',
            },
          });
        }
        insertIndex = bmEnd;
        break;
      }

      case 'image': {
        if (block.meta.url) {
          requests.push({
            insertInlineImage: {
              uri: block.meta.url,
              location: { index: insertIndex },
              objectSize: { width: { magnitude: 400, unit: 'PT' } },
            },
          });
          insertIndex++; // 이미지는 1 인덱스 차지
          // 이미지 후 줄바꿈
          const nlText = '\n';
          requests.push({ insertText: { location: { index: insertIndex }, text: nlText } });
          insertIndex++;
        }
        break;
      }

      case 'table': {
        const { rowCount, colCount, rows } = block.meta;
        if (rowCount > 0 && colCount > 0) {
          // 테이블 위치에 플레이스홀더 삽입, 후처리로 네이티브 표 생성
          const placeholder = `[TABLE_${pendingTables.length}]\n`;
          requests.push({ insertText: { location: { index: insertIndex }, text: placeholder } });
          applyParagraphStyle(requests, insertIndex, insertIndex + placeholder.length, STYLES.paragraph.paragraphStyle, 0);
          pendingTables.push({ placeholderText: placeholder.trim(), rows, rowCount, colCount });
          insertIndex += placeholder.length;
        }
        break;
      }

      default:
        // 알 수 없는 블록 타입 → fallback
        if (block.content) {
          const fbStyle = STYLES.fallback;
          const result = insertTextBlock(requests, insertIndex, block, fbStyle);
          insertIndex = result.endIndex;
        }
    }

  }

  // ── 불릿/넘버드 마커 일괄 적용 ──
  // 연속된 같은 타입의 범위를 병합하여 createParagraphBullets 호출
  const mergedBulletRanges = mergeBulletRanges(bulletRanges);
  for (const range of mergedBulletRanges) {
    requests.push({
      createParagraphBullets: {
        range: { startIndex: range.startIndex, endIndex: range.endIndex },
        bulletPreset: range.preset,
      },
    });
  }

  return { requests, pendingTables };
}

/**
 * 빈 단락 삽입 (콜아웃 전후 여백용, 배경색 없음, 텍스트 1pt)
 */
function insertSpacer(requests, insertIndex, spacePt) {
  const text = ' \n';
  requests.push({ insertText: { location: { index: insertIndex }, text } });
  const start = insertIndex;
  const end = insertIndex + text.length;
  requests.push({
    updateParagraphStyle: {
      range: { startIndex: start, endIndex: end },
      paragraphStyle: {
        namedStyleType: 'NORMAL_TEXT',
        lineSpacing: 100,
        spaceAbove: spacePt,
        spaceBelow: { magnitude: 0, unit: 'PT' },
      },
      fields: 'namedStyleType,lineSpacing,spaceAbove,spaceBelow',
    },
  });
  requests.push({
    updateTextStyle: {
      range: { startIndex: start, endIndex: start + 1 },
      textStyle: { fontSize: { magnitude: 1, unit: 'PT' } },
      fields: 'fontSize',
    },
  });
  return end;
}

/**
 * 테이블 후처리: 플레이스홀더를 네이티브 표로 교체
 * 문서를 재조회하여 플레이스홀더 위치를 찾고, 삭제 후 insertTable + 셀 내용 삽입
 * @param {object} docContent - getDocument() 결과
 * @param {Array} pendingTables - buildRequests()에서 반환된 테이블 정보
 * @returns {Array} batchUpdate 요청 배열 (역순으로 처리해야 인덱스 안 꼬임)
 */
export function buildTableRequests(docContent, pendingTables) {
  if (pendingTables.length === 0) return [];

  const requests = [];
  const elements = docContent.body.content;

  // 플레이스홀더 위치 찾기 (역순 처리를 위해 뒤에서부터)
  const placements = [];
  for (const el of elements) {
    if (!el.paragraph) continue;
    const text = el.paragraph.elements?.map(e => e.textRun?.content || '').join('').trim();
    const match = text?.match(/^\[TABLE_(\d+)\]$/);
    if (match) {
      placements.push({
        tableIndex: parseInt(match[1]),
        startIndex: el.startIndex,
        endIndex: el.endIndex,
      });
    }
  }

  // 역순 처리 (뒤에서부터 교체해야 앞쪽 인덱스가 안 꼬임)
  placements.sort((a, b) => b.startIndex - a.startIndex);

  for (const placement of placements) {
    const table = pendingTables[placement.tableIndex];
    if (!table) continue;

    // 1) 플레이스홀더 삭제
    requests.push({
      deleteContentRange: {
        range: { startIndex: placement.startIndex, endIndex: placement.endIndex },
      },
    });

    // 2) 테이블 삽입
    requests.push({
      insertTable: {
        rows: table.rowCount,
        columns: table.colCount,
        location: { index: placement.startIndex },
      },
    });
  }

  return { requests, placements, pendingTables };
}

/**
 * 테이블 셀 내용 삽입 (insertTable 실행 후 문서 재조회 필요)
 */
export function buildTableCellRequests(docContent, pendingTables) {
  const requests = [];
  const tables = docContent.body.content.filter(el => el.table);

  for (let ti = 0; ti < Math.min(tables.length, pendingTables.length); ti++) {
    const docTable = tables[ti];
    const sourceTable = pendingTables[ti];
    const tableRows = docTable.table?.tableRows;
    if (!tableRows) continue;

    // 역순으로 셀 내용 삽입 (뒤에서부터 해야 인덱스 안 꼬임)
    for (let ri = Math.min(tableRows.length, sourceTable.rowCount) - 1; ri >= 0; ri--) {
      const docRow = tableRows[ri];
      if (!docRow?.tableCells) continue;
      for (let ci = Math.min(docRow.tableCells.length, sourceTable.colCount) - 1; ci >= 0; ci--) {
        const cell = docRow.tableCells[ci];
        const rawCellContent = sourceTable.rows[ri]?.[ci] || '';
        if (!rawCellContent) continue;

        const para = cell?.content?.[0];
        if (!para?.startIndex) continue;

        // 인라인 마크다운 파싱
        const segments = parseInlineMarkdown(rawCellContent);
        const plainText = segments.map(s => s.text).join('');
        if (!plainText) continue;

        requests.push({
          insertText: { location: { index: para.startIndex }, text: plainText },
        });

        // 기본 텍스트 스타일
        requests.push({
          updateTextStyle: {
            range: { startIndex: para.startIndex, endIndex: para.startIndex + plainText.length },
            textStyle: STYLES.paragraph.textStyle,
            fields: buildTextFields(STYLES.paragraph.textStyle),
          },
        });

        // 첫 행 볼드
        if (ri === 0) {
          requests.push({
            updateTextStyle: {
              range: { startIndex: para.startIndex, endIndex: para.startIndex + plainText.length },
              textStyle: { bold: true },
              fields: 'bold',
            },
          });
        }

        // 인라인 서식 오버레이
        let segOffset = para.startIndex;
        for (const seg of segments) {
          const segStart = segOffset;
          const segEnd = segOffset + seg.text.length;
          if (seg.styles.bold) {
            requests.push({ updateTextStyle: { range: { startIndex: segStart, endIndex: segEnd }, textStyle: { bold: true }, fields: 'bold' } });
          }
          if (seg.styles.italic) {
            requests.push({ updateTextStyle: { range: { startIndex: segStart, endIndex: segEnd }, textStyle: { italic: true }, fields: 'italic' } });
          }
          segOffset = segEnd;
        }
      }
    }
  }

  return requests;
}

// ── 내부 헬퍼 ──

function insertTextBlock(requests, insertIndex, block, style) {
  const segments = block.segments || [{ text: block.content, styles: {} }];
  const fullText = segments.map(s => s.text).join('') + '\n';

  // 1) 텍스트 삽입
  requests.push({ insertText: { location: { index: insertIndex }, text: fullText } });

  const startIndex = insertIndex;
  const endIndex = insertIndex + fullText.length;

  // 2) 단락 스타일
  applyParagraphStyle(requests, startIndex, endIndex, style.paragraphStyle, block.depth);

  // 3) 기본 텍스트 스타일 (전체 범위)
  applyTextStyle(requests, startIndex, endIndex - 1, style.textStyle);

  // 4) 인라인 서식 오버레이 — 세그먼트별 스타일을 단일 요청으로 병합
  let segOffset = startIndex;
  for (const seg of segments) {
    const segStart = segOffset;
    const segEnd = segOffset + seg.text.length;
    const mergedStyle = {};
    const fields = [];

    if (seg.styles.bold) {
      mergedStyle.bold = true;
      fields.push('bold');
    }
    for (const prop of ['italic', 'underline', 'strikethrough']) {
      if (seg.styles[prop]) { mergedStyle[prop] = true; fields.push(prop); }
    }
    if (seg.styles.code) {
      Object.assign(mergedStyle, STYLES.inline_code.textStyle);
      fields.push(...Object.keys(STYLES.inline_code.textStyle));
    }
    if (seg.styles.link && seg.link) {
      Object.assign(mergedStyle, STYLES.link.textStyle, { link: { url: seg.link } });
      fields.push(...Object.keys(STYLES.link.textStyle), 'link');
    }
    if (seg.styles.color) {
      const colorName = seg.styles.color;
      // _bg/_background 접미사 → 배경색, 그 외 → 텍스트 색
      const bgName = colorName.endsWith('_bg') ? colorName.replace('_bg', '_background') : colorName;
      if (NOTION_BG_COLORS[bgName]) {
        mergedStyle.backgroundColor = { color: { rgbColor: NOTION_BG_COLORS[bgName] } };
        fields.push('backgroundColor');
      } else if (NOTION_COLORS[colorName]) {
        mergedStyle.foregroundColor = { color: { rgbColor: NOTION_COLORS[colorName] } };
        fields.push('foregroundColor');
      }
    }

    if (fields.length > 0) {
      requests.push({
        updateTextStyle: {
          range: { startIndex: segStart, endIndex: segEnd },
          textStyle: mergedStyle,
          fields: [...new Set(fields)].join(','),
        },
      });
    }

    segOffset = segEnd;
  }

  return { startIndex, endIndex };
}

function applyParagraphStyle(requests, startIndex, endIndex, paragraphStyle, depth) {
  const style = { ...paragraphStyle };

  // 들여쓰기 적용
  if (depth > 0) {
    style.indentStart = { magnitude: depth * INDENT_PER_LEVEL, unit: 'PT' };
  }

  const fields = buildParagraphFields(style);
  if (fields) {
    requests.push({
      updateParagraphStyle: {
        range: { startIndex, endIndex },
        paragraphStyle: style,
        fields,
      },
    });
  }
}

function applyTextStyle(requests, startIndex, endIndex, textStyle) {
  const fields = buildTextFields(textStyle);
  if (fields && startIndex < endIndex) {
    requests.push({
      updateTextStyle: {
        range: { startIndex, endIndex },
        textStyle,
        fields,
      },
    });
  }
}

function buildCalloutStyle(baseStyle, notionColor) {
  const result = {
    textStyle: { ...baseStyle.textStyle },
    paragraphStyle: { ...baseStyle.paragraphStyle },
  };

  // Notion 배경색을 shading에 반영
  if (notionColor && NOTION_BG_COLORS[notionColor]) {
    const bgColor = NOTION_BG_COLORS[notionColor];
    result.paragraphStyle = {
      ...result.paragraphStyle,
      shading: { backgroundColor: { color: { rgbColor: bgColor } } },
    };
  }

  return result;
}

function mergeBulletRanges(ranges) {
  if (ranges.length === 0) return [];

  const merged = [];
  let current = { ...ranges[0] };

  for (let i = 1; i < ranges.length; i++) {
    const next = ranges[i];
    // 같은 타입이고 연속된 범위면 병합
    if (next.type === current.type && next.startIndex === current.endIndex) {
      current.endIndex = next.endIndex;
    } else {
      merged.push(current);
      current = { ...next };
    }
  }
  merged.push(current);

  return merged;
}
