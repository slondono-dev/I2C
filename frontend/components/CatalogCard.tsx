"use client";
import { useState } from "react";
import { Copy, QrCode, ExternalLink, Check } from "lucide-react";
import type { Catalog } from "@/lib/types";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import { errMsg } from "@/lib/format";

export function publicUrlOf(c: Catalog): string {
  if (typeof window !== "undefined") return `${window.location.origin}/c/${c.slug}`;
  return c.public_url;
}

export function CatalogCard({ catalog, onChange }: { catalog: Catalog; onChange: (c: Catalog) => void }) {
  const toast = useToast();
  const [qr, setQr] = useState<string | null>(null);
  const [qrOpen, setQrOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const published = catalog.status === "published";
  const url = publicUrlOf(catalog);

  async function copy() {
    try { await navigator.clipboard.writeText(url); setCopied(true); toast("Link copiado"); setTimeout(() => setCopied(false), 2000); }
    catch { toast("No pudimos copiar el link", "error"); }
  }
  async function showQr() {
    setQrOpen(true);
    if (!qr) { try { setQr(await api.catalogQr(catalog.id)); } catch (e) { toast(errMsg(e), "error"); setQrOpen(false); } }
  }
  async function publish() {
    setBusy(true);
    try { const c = await api.publishCatalog(catalog.id); onChange(c); toast("¡Catálogo publicado!"); }
    catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }

  return (
    <Card className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold">{catalog.name}</h2>
          <p className="text-sm text-stone-500">{catalog.product_count} productos</p>
        </div>
        <Badge tone={published ? "green" : "amber"}>{published ? "Publicado" : "Borrador"}</Badge>
      </div>
      {!published && (
        <div className="rounded-2xl bg-amber-50 p-3 text-sm text-amber-900">
          Tu link público solo funcionará cuando publiques el catálogo.
          <Button className="mt-3 w-full" onClick={publish} disabled={busy}>{busy ? "Publicando..." : "Publicar catálogo"}</Button>
        </div>
      )}
      <div className="flex items-center gap-2 rounded-xl bg-stone-50 px-3 py-2 text-sm">
        <span className="min-w-0 flex-1 truncate text-stone-600">{url}</span>
        <button onClick={copy} aria-label="Copiar link" className="rounded-lg p-2 hover:bg-stone-200">{copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}</button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" onClick={showQr}><QrCode className="h-4 w-4" /> Ver QR</Button>
        <a href={`/c/${catalog.slug}`} target="_blank" rel="noopener noreferrer" className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-stone-300 bg-white px-4 text-sm font-semibold hover:bg-stone-50"><ExternalLink className="h-4 w-4" /> Abrir</a>
      </div>
      <Dialog open={qrOpen} onClose={() => setQrOpen(false)} title="Código QR">
        <div className="flex flex-col items-center gap-3">
          {qr ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={qr} alt="Código QR del catálogo" className="h-64 w-64" /> : <div className="h-64 w-64 animate-pulse rounded-2xl bg-stone-200" />}
          <p className="text-center text-xs text-stone-500">Imprímelo o compártelo para que te escaneen.</p>
        </div>
      </Dialog>
    </Card>
  );
}
