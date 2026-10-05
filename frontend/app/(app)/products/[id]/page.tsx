"use client";
import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Sparkles, Eraser, Trash2, Plus, X } from "lucide-react";
import { api } from "@/lib/api";
import { useProductPolling } from "@/hooks/useProductPolling";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input, Label, Textarea } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs } from "@/components/ui/tabs";
import { Dialog } from "@/components/ui/dialog";
import { STATUS_LABEL, errMsg } from "@/lib/format";
import type { Product, Variant } from "@/lib/types";

type AT = "original" | "clean" | "model" | "lifestyle";
const LABEL: Record<string, string> = { original: "Original", clean: "Sin fondo", model: "Modelo", lifestyle: "Estilo" };
const FIELDS: [keyof Product, string][] = [
  ["category", "Categoría"], ["subcategory", "Subcategoría"], ["color", "Color"], ["gender", "Género"],
  ["size", "Talla"], ["material", "Material"], ["fit", "Corte"], ["sku", "SKU"],
];

export default function ProductDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const toast = useToast();
  const [p, setP] = useState<Product | null>(null);
  const [f, setF] = useState<Record<string, string>>({});
  const [variants, setVariants] = useState<Variant[]>([]);
  const [view, setView] = useState<AT>("original");
  const [busy, setBusy] = useState<string | null>(null);
  const [confirmDel, setConfirmDel] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback((prod: Product) => {
    setP(prod);
    setF({ name: prod.name ?? "", description: prod.description ?? "", price: prod.price ? String(parseFloat(prod.price)) : "", stock: String(prod.stock ?? 0),
      ...Object.fromEntries(FIELDS.map(([k]) => [k, (prod[k] as string | null) ?? ""])) });
    setVariants(prod.variants.map((v) => ({ ...v })));
    setView(prod.primary_asset_type === "clean" && prod.assets.some((a) => a.type === "clean") ? "clean" : "original");
  }, []);
  useEffect(() => { api.product(id).then(load).catch((e) => setErr(errMsg(e))); }, [id, load]);
  useProductPolling(p ? [p] : [], (n) => { setP(n); setF((o) => ({ ...o, name: o.name || n.name || "", description: o.description || n.description || "" })); });

  // keep polling background removal / analysis jobs: refresh product after action
  async function refreshSoon() {
    for (let i = 0; i < 40; i++) {
      await new Promise((r) => setTimeout(r, 1500));
      try {
        const jobs = await api.jobs(id);
        if (!jobs.some((j) => j.status === "pending" || j.status === "running")) break;
      } catch { break; }
    }
    const n = await api.product(id); load(n);
  }

  const asset = (t: string) => p?.assets.find((a) => a.type === t)?.url;
  const available = (["original", "clean", "model", "lifestyle"] as AT[]).filter((t) => asset(t));
  const img = asset(view) ?? p?.display_image ?? null;

  function body() {
    return {
      name: f.name, description: f.description, price: f.price === "" ? null : Number(f.price), stock: parseInt(f.stock || "0", 10),
      ...Object.fromEntries(FIELDS.map(([k]) => [k, f[k] || null])),
      variants: variants.filter((v) => v.size || v.color).map((v) => ({ size: v.size || null, color: v.color || null, stock: Number(v.stock) || 0, sku: v.sku || null })),
    };
  }
  async function patch(extra: Record<string, unknown> = {}, msg = "Guardado") {
    setBusy("save"); setErr("");
    try { const n = await api.updateProduct(id, { ...body(), ...extra } as never); load(n); toast(msg); return true; }
    catch (e) { setErr(errMsg(e)); toast(errMsg(e), "error"); return false; } finally { setBusy(null); }
  }
  async function action(kind: "analyze" | "bg") {
    setBusy(kind);
    try {
      if (kind === "analyze") await api.analyze(id, true); else await api.removeBackground(id);
      toast(kind === "analyze" ? "Analizando de nuevo..." : "Quitando el fondo...");
      const n = await api.product(id); setP(n);
      await refreshSoon();
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(null); }
  }
  async function remove() {
    try { await api.deleteProduct(id); toast("Producto eliminado"); router.replace("/products"); } catch (e) { toast(errMsg(e), "error"); }
  }

  if (!p) return err ? <Card className="text-red-700">{err}</Card> : <div className="mx-auto max-w-md space-y-3"><Skeleton className="aspect-square" /><Skeleton className="h-12" /><Skeleton className="h-12" /></div>;
  const published = p.status === "published";
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF((o) => ({ ...o, [k]: e.target.value }));

  return (
    <div className="mx-auto max-w-3xl space-y-5 pb-24">
      <div className="flex items-center gap-3">
        <Link href="/products" aria-label="Volver" className="rounded-full p-2 hover:bg-stone-100"><ArrowLeft className="h-5 w-5" /></Link>
        <h1 className="flex-1 truncate text-xl font-black">{p.name || "Nuevo producto"}</h1>
        <Badge tone={published ? "green" : p.status === "processing" ? "blue" : "amber"}>{STATUS_LABEL[p.status]}</Badge>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <div className="space-y-3">
          <div className="relative aspect-square overflow-hidden rounded-3xl bg-stone-100">
            {p.status === "processing" && <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/60 text-sm font-semibold text-indigo-700">Analizando producto...</div>}
            {img ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={img} alt={p.name ?? ""} className="h-full w-full object-contain" /> : <Skeleton className="h-full w-full" />}
          </div>
          {available.length > 0 && (
            <div className="space-y-2">
              <Tabs value={view} onChange={setView} items={available.map((t) => ({ value: t, label: LABEL[t] }))} />
              <div className="flex items-center gap-2 text-sm">
                <span className="text-stone-500">Foto en el catálogo:</span>
                {p.primary_asset_type === view ? <Badge tone="green">Esta foto</Badge> : <Button size="sm" variant="outline" onClick={() => patch({ primary_asset_type: view }, "Foto del catálogo actualizada")}>Usar esta</Button>}
              </div>
            </div>
          )}
          <div className="grid grid-cols-2 gap-2">
            <Button variant="secondary" disabled={!!busy} onClick={() => action("analyze")}><Sparkles className="h-4 w-4" />{busy === "analyze" ? "Analizando..." : "Re-analizar"}</Button>
            <Button variant="secondary" disabled={!!busy} onClick={() => action("bg")}><Eraser className="h-4 w-4" />{busy === "bg" ? "Procesando..." : "Quitar fondo"}</Button>
          </div>
        </div>

        <div className="space-y-4">
          <div><Label>Nombre</Label><Input value={f.name} onChange={set("name")} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label>Precio (COP)</Label><Input type="number" inputMode="decimal" min="0" value={f.price} onChange={set("price")} className="h-14 text-xl font-bold" /></div>
            <div><Label>Stock</Label><Input type="number" inputMode="numeric" min="0" value={f.stock} onChange={set("stock")} className="h-14 text-xl font-bold" /></div>
          </div>
          <div><Label>Descripción</Label><Textarea value={f.description} onChange={set("description")} /></div>
          <div className="grid grid-cols-2 gap-3">
            {FIELDS.map(([k, label]) => <div key={k}><Label>{label}</Label><Input value={f[k] ?? ""} onChange={set(k)} className="h-11" /></div>)}
          </div>

          <div>
            <div className="mb-1 flex items-center justify-between"><Label className="mb-0">Tallas y stock</Label>
              <button className="flex items-center gap-1 text-sm font-semibold text-accent" onClick={() => setVariants((v) => [...v, { size: "", stock: 0 }])}><Plus className="h-4 w-4" />Agregar</button></div>
            <div className="space-y-2">
              {variants.map((v, i) => (
                <div key={i} className="flex gap-2">
                  <Input placeholder="Talla" value={v.size ?? ""} onChange={(e) => setVariants((s) => s.map((x, j) => (j === i ? { ...x, size: e.target.value } : x)))} className="h-11" />
                  <Input placeholder="Stock" type="number" min="0" value={v.stock} onChange={(e) => setVariants((s) => s.map((x, j) => (j === i ? { ...x, stock: Number(e.target.value) } : x)))} className="h-11 w-24" />
                  <button aria-label="Quitar" onClick={() => setVariants((s) => s.filter((_, j) => j !== i))} className="rounded-xl p-2 text-stone-400 hover:bg-stone-100"><X className="h-5 w-5" /></button>
                </div>
              ))}
            </div>
          </div>
          {err && <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{err}</p>}
        </div>
      </div>

      <div className="fixed inset-x-0 bottom-20 z-20 mx-auto flex max-w-3xl gap-2 px-4 md:bottom-4">
        <Button size="lg" variant="outline" className="flex-1 bg-white" disabled={!!busy} onClick={() => patch()}>{busy === "save" ? "Guardando..." : "Guardar"}</Button>
        <Button size="lg" className="flex-1" disabled={!!busy} onClick={() => patch({ status: published ? "draft" : "published" }, published ? "Despublicado" : "¡Publicado!")}>{published ? "Despublicar" : "Publicar"}</Button>
        <Button size="lg" variant="ghost" aria-label="Eliminar" className="bg-white text-red-600" onClick={() => setConfirmDel(true)}><Trash2 className="h-5 w-5" /></Button>
      </div>
      <Dialog open={confirmDel} onClose={() => setConfirmDel(false)} title="¿Eliminar producto?">
        <p className="mb-4 text-sm text-stone-600">Esta acción no se puede deshacer.</p>
        <div className="flex gap-2"><Button variant="outline" className="flex-1" onClick={() => setConfirmDel(false)}>Cancelar</Button><Button variant="danger" className="flex-1" onClick={remove}>Eliminar</Button></div>
      </Dialog>
    </div>
  );
}
