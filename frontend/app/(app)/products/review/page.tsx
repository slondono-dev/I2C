"use client";
import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useProductPolling } from "@/hooks/useProductPolling";
import { useToast } from "@/components/ui/toast";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { errMsg } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Product } from "@/lib/types";

type Edit = { name: string; price: string; stock: string; sku: string };

function reviewImage(p: Product): string | null {
  return p.assets.find((a) => a.type === "clean")?.url ?? p.assets.find((a) => a.type === "original")?.url ?? p.display_image;
}
const toEdit = (p: Product): Edit => ({ name: p.name ?? "", price: p.price ? String(parseFloat(p.price)) : "", stock: String(p.stock ?? 0), sku: p.sku ?? "" });

function ReviewInner() {
  const sp = useSearchParams();
  const idsParam = sp.get("ids");
  const { catalog, loading: wsLoading } = useWorkspace();
  const toast = useToast();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [edits, setEdits] = useState<Record<string, Edit>>({});
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);

  const merge = useCallback((list: Product[], keepEdits = false) => {
    setProducts(list);
    setEdits((e) => { const n = { ...e }; list.forEach((p) => { if (!keepEdits || !n[p.id]) n[p.id] = toEdit(p); }); return n; });
  }, []);

  useEffect(() => {
    (async () => {
      try {
        if (idsParam) {
          const list = await Promise.all(idsParam.split(",").filter(Boolean).map((id) => api.product(id).catch(() => null)));
          merge(list.filter(Boolean) as Product[]);
        } else if (catalog) {
          const lists = await Promise.all(["processing", "review", "draft"].map((s) => api.products({ catalog_id: catalog.id, status_: s })));
          merge(lists.flat());
        } else if (!wsLoading) setProducts([]);
      } catch (e) { toast(errMsg(e), "error"); setProducts([]); }
    })();
  }, [idsParam, catalog, wsLoading, merge, toast]);

  useProductPolling(products ?? [], (p) => {
    setProducts((s) => s?.map((x) => (x.id === p.id ? p : x)) ?? s);
    setEdits((e) => ({ ...e, [p.id]: toEdit(p) }));
  });

  const setField = (id: string, k: keyof Edit, v: string) => setEdits((e) => ({ ...e, [id]: { ...e[id], [k]: v } }));
  const toggle = (id: string) => setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });

  function payload(id: string) {
    const e = edits[id];
    const out: { id: string; name?: string; price?: number; stock?: number; sku?: string } = { id, name: e.name };
    if (e.price !== "") out.price = Number(e.price);
    if (e.stock !== "") out.stock = parseInt(e.stock, 10);
    if (e.sku) out.sku = e.sku;
    return out;
  }

  async function saveOne(id: string) {
    setSaving(id);
    try {
      const [u] = await api.bulkUpdate([payload(id)]);
      if (u) setProducts((s) => s?.map((x) => (x.id === id ? u : x)) ?? s);
      setErrors((e) => { const n = { ...e }; delete n[id]; return n; });
      toast("Guardado");
    } catch (e) { setErrors((s) => ({ ...s, [id]: errMsg(e) })); } finally { setSaving(null); }
  }

  async function publishSelected() {
    const ids = Array.from(sel);
    if (!ids.length) return;
    setBusy(true); setErrors({});
    try {
      await api.bulkUpdate(ids.map(payload));
      const r = await api.bulkPublish(ids);
      const errs: Record<string, string> = {};
      r.errors.forEach((x) => { errs[x.id] = x.error; });
      setErrors(errs);
      if (r.published.length) {
        toast(`${r.published.length} ${r.published.length === 1 ? "producto publicado" : "productos publicados"}`);
        setProducts((s) => s?.filter((p) => !r.published.includes(p.id)) ?? s);
        setSel((s) => { const n = new Set(s); r.published.forEach((i) => n.delete(i)); return n; });
      }
      if (r.errors.length) toast("Algunos productos necesitan datos (nombre, precio o foto)", "error");
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }

  const ready = (products ?? []).filter((p) => p.status !== "processing");

  return (
    <div className="mx-auto max-w-2xl space-y-4 pb-24">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-black">Revisar productos</h1>
        {ready.length > 0 && (
          <button className="text-sm font-semibold text-accent" onClick={() => setSel(sel.size === ready.length ? new Set() : new Set(ready.map((p) => p.id)))}>
            {sel.size === ready.length ? "Quitar todo" : "Seleccionar todo"}
          </button>
        )}
      </div>

      {products === null && [0, 1].map((i) => <Skeleton key={i} className="h-72" />)}
      {products?.length === 0 && (
        <Card className="space-y-3 py-10 text-center">
          <p className="text-stone-600">No hay productos por revisar.</p>
          <Link href="/products/new" className={cn(buttonVariants(), "mx-auto")}>Agregar productos</Link>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {products?.map((p) => {
          const e = edits[p.id];
          if (p.status === "processing") {
            return (
              <Card key={p.id} className="space-y-3">
                <Skeleton className="aspect-[4/3] w-full" /><Skeleton className="h-5 w-2/3" />
                <p className="text-sm text-indigo-600">Analizando producto...</p>
              </Card>
            );
          }
          const img = reviewImage(p);
          const chips = [p.category, p.color, p.fit, p.gender, p.material].filter(Boolean) as string[];
          return (
            <Card key={p.id} className={cn("space-y-3", sel.has(p.id) && "ring-2 ring-accent")}>
              <div className="relative">
                {img ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={img} alt={p.name ?? "Producto"} loading="lazy" className="aspect-[4/3] w-full rounded-2xl bg-stone-100 object-contain" /> : <Skeleton className="aspect-[4/3] w-full" />}
                <label className="absolute left-2 top-2 flex h-9 w-9 items-center justify-center rounded-full bg-white/90 shadow">
                  <input type="checkbox" className="h-5 w-5 accent-indigo-600" checked={sel.has(p.id)} onChange={() => toggle(p.id)} aria-label="Seleccionar" />
                </label>
                <Link href={`/products/${p.id}`} className="absolute right-2 top-2 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold shadow">Editar</Link>
              </div>
              <input value={e?.name ?? ""} onChange={(ev) => setField(p.id, "name", ev.target.value)} placeholder="Nombre del producto"
                className="h-12 w-full rounded-xl border border-stone-300 px-3 text-base font-semibold focus:border-accent focus:outline-none" />
              {chips.length > 0 && <div className="flex flex-wrap gap-1.5">{chips.map((c) => <Badge key={c}>{c}</Badge>)}</div>}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-stone-500">Precio</label>
                  <input inputMode="decimal" type="number" min="0" value={e?.price ?? ""} onChange={(ev) => setField(p.id, "price", ev.target.value)} placeholder="$0"
                    className="h-14 w-full rounded-xl border border-stone-300 px-3 text-xl font-bold focus:border-accent focus:outline-none" />
                </div>
                <div>
                  <label className="text-xs font-medium text-stone-500">Stock</label>
                  <input inputMode="numeric" type="number" min="0" value={e?.stock ?? ""} onChange={(ev) => setField(p.id, "stock", ev.target.value)}
                    className="h-14 w-full rounded-xl border border-stone-300 px-3 text-xl font-bold focus:border-accent focus:outline-none" />
                </div>
              </div>
              <input value={e?.sku ?? ""} onChange={(ev) => setField(p.id, "sku", ev.target.value)} placeholder="SKU (opcional)"
                className="h-10 w-full rounded-xl border border-stone-200 px-3 text-sm focus:border-accent focus:outline-none" />
              {errors[p.id] && <p role="alert" className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{errors[p.id]}</p>}
              <Button variant="secondary" className="w-full" disabled={saving === p.id} onClick={() => saveOne(p.id)}>{saving === p.id ? "Guardando..." : "Guardar"}</Button>
            </Card>
          );
        })}
      </div>

      {sel.size > 0 && (
        <div className="fixed inset-x-0 bottom-20 z-20 mx-auto max-w-2xl px-4 md:bottom-4">
          <Button size="xl" className="w-full shadow-2xl" disabled={busy} onClick={publishSelected}>
            {busy ? "Publicando..." : `Publicar seleccionados (${sel.size})`}
          </Button>
        </div>
      )}
    </div>
  );
}

export default function ReviewPage() {
  return <Suspense fallback={<Skeleton className="mx-auto h-72 max-w-2xl" />}><ReviewInner /></Suspense>;
}
