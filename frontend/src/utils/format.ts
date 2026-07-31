export function clampQualityScore(score: number): number {
  return Math.min(100, Math.max(0, score));
}

export function formatQualityScore(score: number): string {
  return clampQualityScore(score).toFixed(1).replace(/\.0$/, "");
}
