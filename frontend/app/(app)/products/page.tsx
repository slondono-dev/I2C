"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useWorkspace } from "@/hooks/useWorkspace";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { buttonVariants } from "@/components/ui/button";
import { STATUS_LABEL, formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Product } from "@/lib/types";

const tone = (s: string) => (s === "published" ? "green" : s === "processing" ? "blue" : s === "review" ? "amber" : "neutral");
function thumb(p: Product) { return p.assets.find((a) => a.type === "thumbnail")?.url ?? p.display_image; }

export default function Products() {
  const { catalog, loading } = useWorkspace();
  const [all, setAll] = useState<Product[] | null>(null);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [low, setLow] = useState(false);

  useEffect(() => {
    if (!catalog) return;
    api.products({ catalog_id: catalog.id }).then(setAll).catch(() => setAll([]));
  }, [catalog]);

  const categories = useMemo(() => Array.from(new Set((all ?? []).map((p) => p.category).filter(Boolean) as string[])), [all]);
  const list = (all ?? []).filter((p) => (!category || p.category === category) && (!status || p.status === status) && (!low || (p.stock_mode === "tracked" && p.stock <= 5)));
  const sel = "h-10 rounded-xl border border-stone-300 bg-white px-3 text-sm";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-2xl font-black">Productos</h1>
        <Link href="/products/review" className="text-sm font-semibold text-accent">Revisar</Link></div>
      <div className="flex flex-wrap gap-2">
        <select aria-label="Categoría" className={sel} value={category} onChange={(e) => setCategory(e.target.value)}><option value="">Categoría</option>{categories.map((c) => <option key={c}>{c}</option>)}</select>
        <select aria-label="Estado" className={sel} value={status} onChange={(e) => setStatus(e.target.value)}><option value="">Estado</option>{Object.entries(STATUS_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        <label className={cn(sel, "flex items-center gap-2")}><input type="checkbox" checked={low} onChange={(e) => setLow(e.target.checked)} /> Stock bajo</label>
      </div>

      {(loading || all === null) && <div className="space-y-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-20" />)}</div>}
      {all && list.length === 0 && (
        <Card className="space-y-3 py-10 text-center"><p className="text-stone-600">{all.length ? "No hay productos con esos filtros." : "Aún no tienes productos."}</p>
          <Link href="/products/new" className={cn(buttonVariants(), "mx-auto")}>Agregar productos</Link></Card>
      )}

      <div className="space-y-3 md:hidden">
        {list.map((p) => (
          <Link key={p.id} href={`/products/${p.id}`}>
            <Card className="mb-3 flex items-center gap-3 p-3">
              <Thumb p={p} />
              <div className="min-w-0 flex-1"><div className="truncate font-semibold">{p.name || "Sin nombre"}</div>
                <div className="text-sm text-stone-500">{formatPrice(p.price, p.currency) || "Sin precio"} · {p.stock} u.</div></div>
              <Badge tone={tone(p.status)}>{STATUS_LABEL[p.status]}</Badge>
            </Card>
          </Link>
        ))}
      </div>
      {list.length > 0 && (
        <table className="hidden w-full overflow-hidden rounded-2xl border border-stone-200 bg-white text-sm md:table">
          <thead className="bg-stone-50 text-left text-xs uppercase text-stone-500"><tr><th className="p-3">Producto</th><th>Precio</th><th>Stock</th><th>Estado</th></tr></thead>
          <tbody>{list.map((p) => (
            <tr key={p.id} className="border-t border-stone-100 hover:bg-stone-50">
              <td className="p-3"><Link href={`/products/${p.id}`} className="flex items-center gap-3"><Thumb p={p} small /><span className="font-medium">{p.name || "Sin nombre"}</span></Link></td>
              <td>{formatPrice(p.price, p.currency) || "—"}</td><td className={p.stock <= 5 ? "font-semibold text-amber-700" : ""}>{p.stock}</td>
              <td><Badge tone={tone(p.status)}>{STATUS_LABEL[p.status]}</Badge></td>
            </tr>))}</tbody>
        </table>
      )}
    </div>
  );
}

function Thumb({ p, small }: { p: Product; small?: boolean }) {
  const u = thumb(p);
  const size = small ? "h-12 w-12" : "h-16 w-16";
  return <div className={cn("shrink-0 overflow-hidden rounded-xl bg-stone-100", size)}>{/* eslint-disable-next-line @next/next/no-img-element */}{u ? <img src={u} alt="" loading="lazy" className="h-full w-full object-cover" /> : <Skeleton className="h-full w-full" />}</div>;
}
