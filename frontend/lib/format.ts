export function formatPrice(value: string | number | null | undefined, currency = "COP"): string {
  if (value === null || value === undefined || value === "") return "";
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n)) return "";
  try {
    return new Intl.NumberFormat("es-CO", {
      style: "currency", currency, maximumFractionDigits: currency === "COP" ? 0 : 2, minimumFractionDigits: 0,
    }).format(n).replace(/\s/g, "");
  } catch { return `$${n}`; }
}

export const STATUS_LABEL: Record<string, string> = {
  draft: "Borrador", processing: "Analizando", review: "Por revisar", published: "Publicado", archived: "Archivado",
};
export const THEME_LABEL: Record<string, string> = {
  minimal: "Minimal", editorial: "Editorial", street: "Street", premium: "Premium", colorful: "Colorido",
};
export function errMsg(e: unknown, fallback = "Algo salió mal. Inténtalo de nuevo."): string {
  return e instanceof Error && e.message ? e.message : fallback;
}
export function cleanPhone(p: string): string { return p.replace(/[^\d]/g, ""); }
