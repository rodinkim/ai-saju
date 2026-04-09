/**
 * LLM이 자주 내는 깨진 마크다운(특히 CJK + **)을 보정합니다.
 * - 규칙 나열 대신 ** 구분자를 기준으로 열림/닫힘을 구분해 공백만 삽입합니다.
 * - 짝이 맞지 않는 **는 보수적으로 한 번만 처리합니다.
 */

const NEEDS_SPACE_BEFORE_OPEN = /[\uac00-\ud7af\u4e00-\u9fff\u3040-\u30ffA-Za-z0-9)\]」』）]/;

const NEEDS_SPACE_AFTER_CLOSE = /[\uac00-\ud7af\u4e00-\u9fff]/;

function insertSpaceBeforeOpen(beforeChunk) {
  if (!beforeChunk) return beforeChunk;
  const last = beforeChunk.slice(-1);
  if (!last || /\s/.test(last) || last === '*' || last === '\\') return beforeChunk;
  if (!NEEDS_SPACE_BEFORE_OPEN.test(last)) return beforeChunk;
  return `${beforeChunk} `;
}

function insertSpaceAfterClose(afterChunk) {
  if (!afterChunk) return afterChunk;
  if (/^\s/.test(afterChunk)) return afterChunk;
  const first = afterChunk[0];
  if (!NEEDS_SPACE_AFTER_CLOSE.test(first)) return afterChunk;
  return ` ${afterChunk}`;
}

/** 볼드 안쪽( split 후 홀수 인덱스) 앞뒤 공백 제거 — `** 텍스트**` / `**텍스트 **` 보정 */
function trimBoldInnerSegments(parts) {
  return parts.map((chunk, i) => {
    if (i % 2 === 0) return chunk;
    return chunk.replace(/^\s+/, '').replace(/\s+$/, '');
  });
}

/**
 * @param {string} text
 * @returns {string}
 */
export function normalizeLlmMarkdown(text) {
  if (!text || !text.includes('**')) {
    return text?.replace(/\n{3,}/g, '\n\n') ?? text;
  }

  const parts = text.split('**');
  if (parts.length < 2) {
    return text.replace(/\n{3,}/g, '\n\n');
  }

  // 단일 ** 한 쌍만 있는 경우(미닫힘 등): 열림 전 공백 + 볼드 시작 공백 제거
  if (parts.length === 2) {
    const head = insertSpaceBeforeOpen(parts[0]);
    const inner = parts[1].replace(/^\s+/, '').replace(/\s+$/, '');
    return `${head}**${inner}`.replace(/\n{3,}/g, '\n\n');
  }

  // ** 개수가 홀수면 짝이 안 맞음 → 보수적 정규식만 적용
  if (parts.length % 2 === 0) {
    return text
      .replace(
        /([\uac00-\ud7af\u4e00-\u9fff\u3040-\u30ffA-Za-z0-9)\]」』）])\*\*(?=\S)/g,
        '$1 **',
      )
      .replace(/\*\* +(?=\S)/g, '**')
      .replace(
        /([\uac00-\ud7af\u4e00-\u9fff\u3040-\u30ffA-Za-z0-9)\]」』）]) +\*\*(?=\s|$|[\uac00-\ud7af\u4e00-\u9fff])/g,
        '$1**',
      )
      .replace(/\n{3,}/g, '\n\n');
  }

  const segments = trimBoldInnerSegments(parts);

  let out = segments[0];
  for (let i = 1; i < segments.length; i += 1) {
    const isOpening = i % 2 === 1;
    if (isOpening) {
      out = insertSpaceBeforeOpen(out);
      out += '**';
      out += segments[i];
    } else {
      out += '**';
      const rest = insertSpaceAfterClose(segments[i]);
      out += rest;
    }
  }

  return out.replace(/\n{3,}/g, '\n\n');
}
