/**
 * LLM이 자주 내는 `한글**강조**` 형태는 remark가 볼드로 못 읽는 경우가 많아,
 * `**` 짝이 맞을 때만 열림·닫힘 앞뒤에 공백을 넣습니다.
 * 짝이 맞지 않으면 원문을 바꾸지 않습니다(깨진 단일 `**` 보정 제거).
 * 전각 별(U+FF0A) → ASCII `*`, 과도한 빈 줄 정리.
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
function normalizeBoldInSegment(text) {
  if (!text || !text.includes('**')) {
    return text;
  }

  const parts = text.split('**');
  if (parts.length < 2) {
    return text;
  }

  /** 단일 `**`만 있으면 닫힘이 없어 파서가 망가지므로 손대지 않음 */
  if (parts.length === 2) {
    return text;
  }

  /** 짝 안 맞는 `**` 개수면 보정하지 않음 */
  if (parts.length % 2 === 0) {
    return text;
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

  return out;
}

/**
 * @param {string} text
 * @returns {string}
 */
/**
 * 단일 `~`를 이스케이프합니다.
 * `~~취소선~~`은 건드리지 않고, 숫자·텍스트 사이의 `~`(범위 표현)만 `\~`로 변환합니다.
 * 예: `33~40세` → `33\~40세`, `2033~2043년` → `2033\~2043년`
 */
function escapeSingleTilde(text) {
  // `~~`는 취소선으로 유지, 단독 `~`만 이스케이프
  return text.replace(/(?<!~)~(?!~)/g, '\\~');
}

export function normalizeLlmMarkdown(text) {
  if (!text) return text;
  const normalizedStars = text.replace(/\uFF0A/g, '*');

  const lines = normalizedStars.split(/\r?\n/);
  const out = lines
    .map((line) => escapeSingleTilde(line))
    .map((line) => normalizeBoldInSegment(line));

  return out.join('\n').replace(/\n{3,}/g, '\n\n');
}
