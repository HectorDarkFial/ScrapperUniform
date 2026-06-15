export function formatEta(seconds?: number | null): string | null {
  if (seconds == null || seconds < 0) return null;
  if (seconds === 0) return 'casi listo';
  if (seconds < 45) return `~${seconds} s`;
  if (seconds < 3600) return `~${Math.ceil(seconds / 60)} min`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.ceil((seconds % 3600) / 60);
  return mins > 0 ? `~${hours} h ${mins} min` : `~${hours} h`;
}
