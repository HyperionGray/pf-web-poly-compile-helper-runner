export function countWordsMarkdown(text) {
  const cleanText = text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`]*`/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[#*_~`]/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  return cleanText ? cleanText.split(' ').length : 0;
}

