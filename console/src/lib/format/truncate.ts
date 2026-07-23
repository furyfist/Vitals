export function truncateId(id: string | null | undefined, length = 6): string {
  if (!id) return "—";
  if (id.length <= length) return id;
  return `${id.substring(0, length)}…`;
}

export function formatExcerpt(text: string | null | undefined, maxLength = 240): string {
  if (!text) return '""';
  const collapsed = text.replace(/\s+/g, " ").trim();
  if (collapsed.length <= maxLength) {
    return `"${collapsed}"`;
  }
  return `"${collapsed.substring(0, maxLength)}…"`;
}
