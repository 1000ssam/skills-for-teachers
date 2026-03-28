/**
 * Style Map — Notion 블록 유형 → Google Docs 스타일 정의
 *
 * 서식을 변경하려면 이 파일만 수정���면 된다.
 * request-builder.js는 이 맵을 참조할 뿐 스타일 값을 직접 알지 못한다.
 */

// ── 색상 헬퍼 ──────────────────────────────────────────────
function rgb(r, g, b) {
  return { color: { rgbColor: { red: r, green: g, blue: b } } };
}
function pt(n) {
  return { magnitude: n, unit: 'PT' };
}

// ── Notion 색상 → Google Docs rgbColor ─────────────────────
export const NOTION_COLORS = {
  default: null,
  gray: { red: 0.6, green: 0.6, blue: 0.6 },
  brown: { red: 0.6, green: 0.4, blue: 0.2 },
  orange: { red: 0.85, green: 0.45, blue: 0.1 },
  yellow: { red: 0.8, green: 0.68, blue: 0.0 },
  green: { red: 0.2, green: 0.6, blue: 0.2 },
  blue: { red: 0.2, green: 0.4, blue: 0.8 },
  purple: { red: 0.5, green: 0.3, blue: 0.7 },
  pink: { red: 0.8, green: 0.3, blue: 0.5 },
  red: { red: 0.8, green: 0.2, blue: 0.2 },
};

// 배경색 변환 (Notion의 _background 접미사)
export const NOTION_BG_COLORS = {
  gray_background: { red: 0.96, green: 0.96, blue: 0.96 },
  brown_background: { red: 0.97, green: 0.95, blue: 0.93 },
  orange_background: { red: 1.0, green: 0.97, blue: 0.93 },
  yellow_background: { red: 1.0, green: 0.99, blue: 0.93 },
  green_background: { red: 0.94, green: 0.98, blue: 0.94 },
  blue_background: { red: 0.94, green: 0.96, blue: 1.0 },
  purple_background: { red: 0.96, green: 0.94, blue: 1.0 },
  pink_background: { red: 1.0, green: 0.95, blue: 0.97 },
  red_background: { red: 1.0, green: 0.95, blue: 0.94 },
};

// ── 들여쓰기 단위 ──────────────────────────────────────────
export const INDENT_PER_LEVEL = 18; // PT, 0.25인치

// ── 메인 스타일 맵 ─────────────────────────────────────────
export const STYLES = {
  heading_1: {
    textStyle: {
      bold: true,
      fontSize: pt(25),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'HEADING_1',
      spaceAbove: pt(20),
      spaceBelow: pt(6),
      keepLinesTogether: true,
      keepWithNext: true,
    },
  },

  heading_2: {
    textStyle: {
      bold: true,
      fontSize: pt(16),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'HEADING_2',
      spaceAbove: pt(18),
      spaceBelow: pt(6),
      keepLinesTogether: true,
      keepWithNext: true,
    },
  },

  heading_3: {
    textStyle: {
      bold: true,
      fontSize: pt(14),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
      foregroundColor: rgb(0.2901961, 0.5254902, 0.9098039),
    },
    paragraphStyle: {
      namedStyleType: 'HEADING_3',
      spaceAbove: pt(16),
      spaceBelow: pt(4),
      keepLinesTogether: true,
      keepWithNext: true,
    },
  },

  heading_4: {
    textStyle: {
      bold: true,
      underline: true,
      fontSize: pt(12),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
      foregroundColor: rgb(0.06666667, 0.33333334, 0.8),
    },
    paragraphStyle: {
      namedStyleType: 'HEADING_4',
      spaceAbove: pt(14),
      spaceBelow: pt(4),
      keepLinesTogether: true,
      keepWithNext: true,
    },
  },

  paragraph: {
    textStyle: {
      fontSize: pt(10),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 150,
      spaceAbove: pt(10),
      spaceBelow: pt(0),
      spacingMode: 'NEVER_COLLAPSE',
    },
  },

  bulleted_list_item: {
    textStyle: {
      fontSize: pt(10),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 150,
      spaceAbove: pt(0),
      spaceBelow: pt(0),
    },
    bulletPreset: 'BULLET_DISC_CIRCLE_SQUARE',
  },

  numbered_list_item: {
    textStyle: {
      fontSize: pt(10),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 150,
      spaceAbove: pt(0),
      spaceBelow: pt(0),
    },
    bulletPreset: 'NUMBERED_DECIMAL_ALPHA_ROMAN',
  },

  to_do: {
    textStyle: {
      fontSize: pt(10),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 150,
      spaceAbove: pt(0),
      spaceBelow: pt(0),
    },
  },

  toggle: {
    textStyle: {
      bold: true,
      fontSize: pt(10),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 150,
      spaceAbove: pt(6),
      spaceBelow: pt(2),
    },
  },

  quote: {
    textStyle: {
      italic: true,
      fontSize: pt(10),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
      foregroundColor: rgb(0.35, 0.35, 0.35),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 150,
      spaceAbove: pt(8),
      spaceBelow: pt(8),
      borderLeft: {
        color: rgb(0.78, 0.78, 0.78),
        width: pt(3),
        padding: pt(6),
        dashStyle: 'SOLID',
      },
    },
  },

  callout: {
    textStyle: {
      fontSize: pt(10),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 150,
      spaceAbove: pt(0),
      spaceBelow: pt(0),
      shading: { backgroundColor: rgb(0.96, 0.96, 0.96) },
    },
    // 콜아웃 그룹 첫/마지막 블록 여백
    groupSpaceAbove: pt(15),
  },

  code: {
    textStyle: {
      fontSize: pt(9),
      weightedFontFamily: { fontFamily: 'JetBrains Mono', weight: 400 },
      foregroundColor: rgb(0.2, 0.2, 0.2),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      lineSpacing: 100,
      spaceAbove: pt(0),
      spaceBelow: pt(0),
      shading: { backgroundColor: rgb(0.97, 0.97, 0.97) },
    },
  },

  code_label: {
    textStyle: {
      fontSize: pt(8),
      weightedFontFamily: { fontFamily: 'JetBrains Mono', weight: 400 },
      foregroundColor: rgb(0.5, 0.5, 0.5),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      spaceAbove: pt(10),
      spaceBelow: pt(0),
      shading: { backgroundColor: rgb(0.93, 0.93, 0.93) },
    },
  },

  divider: {
    textStyle: {
      fontSize: pt(6),
      foregroundColor: rgb(0.78, 0.78, 0.78),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      alignment: 'CENTER',
      spaceAbove: pt(12),
      spaceBelow: pt(12),
    },
  },

  bookmark: {
    textStyle: {
      fontSize: pt(10),
      underline: true,
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
      foregroundColor: rgb(0.06, 0.33, 0.8),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      spaceAbove: pt(4),
      spaceBelow: pt(4),
    },
  },

  equation: {
    textStyle: {
      italic: true,
      fontSize: pt(11),
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
      foregroundColor: rgb(0.2, 0.2, 0.2),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      alignment: 'CENTER',
      spaceAbove: pt(8),
      spaceBelow: pt(8),
    },
  },

  table_of_contents: {
    textStyle: {
      italic: true,
      fontSize: pt(10),
      foregroundColor: rgb(0.5, 0.5, 0.5),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      spaceAbove: pt(6),
      spaceBelow: pt(6),
    },
  },

  // 미지원/미디어 블록 fallback
  fallback: {
    textStyle: {
      fontSize: pt(10),
      italic: true,
      weightedFontFamily: { fontFamily: 'Arimo', weight: 400 },
      foregroundColor: rgb(0.5, 0.5, 0.5),
    },
    paragraphStyle: {
      namedStyleType: 'NORMAL_TEXT',
      spaceAbove: pt(4),
      spaceBelow: pt(4),
    },
  },

  // 인라인 코드 오버레이
  inline_code: {
    textStyle: {
      weightedFontFamily: { fontFamily: 'JetBrains Mono', weight: 400 },
      fontSize: pt(9.5),
      backgroundColor: rgb(0.94, 0.94, 0.94),
    },
  },

  // 링크 오버레이
  link: {
    textStyle: {
      underline: true,
      foregroundColor: rgb(0.06, 0.33, 0.8),
    },
  },
};
