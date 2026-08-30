/** Public asset URL that respects Vite base path (GitHub Pages project site). */
export function assetUrl(path: string): string {
  const normalized = path.startsWith("/") ? path.slice(1) : path;
  return `${import.meta.env.BASE_URL}${normalized}`;
}
