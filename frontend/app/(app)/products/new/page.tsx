"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Camera, ImagePlus, Check, X, Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useWorkspace } from "@/hooks/useWorkspace";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { Product } from "@/lib/types";

type State = "queued" | "uploading" | "analyzing" | "done" | "error";
type Item = { key: string; name: string; preview: string; state: State; product?: Product; startedAt?: number; message?: string };

const MAX_PARALLEL = 4;
const MAX_MB = 12;
const POLL_MAX_MS = 90000;

function thumb(p?: Product): string | null {
  if (!p) return null;
  return p.assets.find((a) => a.type === "thumbnail")?.url ?? p.assets.find((a) => a.type === "original")?.url ?? p.display_image;
}

export default function NewProducts() {
  const { catalog, catalogs, selectCatalog, loading } = useWorkspace();
  const [items, setItems] = useState<Item[]>([]);
  const camRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const queue = useRef<{ key: string; file: File }[]>([]);
  const running = useRef(0);
  const catalogId = useRef<string | null>(null);
  catalogId.current = catalog?.id ?? null;

  const patch = useCallback((key: string, p: Partial<Item>) => setItems((s) => s.map((i) => (i.key === key ? { ...i, ...p } : i))), []);

  const pump = useCallback(() => {
    while (running.current < MAX_PARALLEL && queue.current.length && catalogId.current) {
      const job = queue.current.shift()!;
      running.current++;
      patch(job.key, { state: "uploading" });
      api.uploadProduct(catalogId.current, job.file, true)
        .then((p) => patch(job.key, p.status === "processing" ? { state: "analyzing", product: p, startedAt: Date.now() } : { state: "done", product: p }))
        .catch(() => patch(job.key, { state: "error", message: "No pudimos subir esta foto. Inténtalo de nuevo." }))
        .finally(() => { running.current--; pump(); });
    }
  }, [patch]);

  function addFiles(list: FileList | null) {
    if (!list?.length) return;
    const fresh: Item[] = [];
    Array.from(list).forEach((f) => {
      const key = `${f.name}-${f.size}-${Math.random().toString(36).slice(2)}`;
      if (!f.type.startsWith("image/") || f.size > MAX_MB * 1024 * 1024) {
        fresh.push({ key, name: f.name, preview: "", state: "error", message: `Usa una imagen JPG, PNG o WebP de máximo ${MAX_MB}MB.` });
        return;
      }
      fresh.push({ key, name: f.name, preview: URL.createObjectURL(f), state: "queued" });
      queue.current.push({ key, file: f });
    });
    setItems((s) => [...fresh, ...s]);
    pump();
  }

  // Poll analyzing items
  const analyzingIds = items.filter((i) => i.state === "analyzing").map((i) => i.key).join(",");
  const itemsRef = useRef(items);
  itemsRef.current = items;
  useEffect(() => {
    if (!analyzingIds) return;
    const t = setInterval(async () => {
      for (const it of itemsRef.current.filter((i) => i.state === "analyzing" && i.product)) {
        if (Date.now() - (it.startedAt ?? 0) > POLL_MAX_MS) { patch(it.key, { state: "error", message: "Está tardando más de lo normal." }); continue; }
        try {
          const p = await api.product(it.product!.id);
          if (p.status !== "processing") patch(it.key, { state: "done", product: p });
        } catch { /* retry next tick */ }
      }
    }, 1500);
    return () => clearInterval(t);
  }, [analyzingIds, patch]);

  const doneCount = items.filter((i) => i.state === "done").length;
  const pending = items.filter((i) => ["queued", "uploading", "analyzing"].includes(i.state)).length;
  const ids = items.filter((i) => i.product && (i.state === "done" || i.state === "error")).map((i) => i.product!.id);

  return (
    <div className="mx-auto max-w-md space-y-5">
      <h1 className="text-2xl font-black">Agregar productos</h1>
      <input ref={camRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
      <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp,image/*" multiple className="hidden" onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
      {loading ? <Skeleton className="h-40" /> : (
        <>
          {catalogs.length > 1 && (
            <div className="flex gap-2 overflow-x-auto" role="radiogroup" aria-label="Catálogo">
              {catalogs.map((c) => (
                <button key={c.id} role="radio" aria-checked={catalog?.id === c.id} onClick={() => selectCatalog(c.id)}
                  className={cn("shrink-0 rounded-full border px-4 py-2 text-sm font-semibold", catalog?.id === c.id ? "border-accent bg-accent text-white" : "border-stone-300 bg-white")}>{c.name}</button>
              ))}
            </div>
          )}
          <button onClick={() => camRef.current?.click()} disabled={!catalog}
            className="flex h-44 w-full flex-col items-center justify-center gap-3 rounded-3xl bg-accent text-white shadow-xl shadow-indigo-200 transition active:scale-[0.98] disabled:opacity-50">
            <Camera className="h-14 w-14" /><span className="text-lg font-bold">Tomar foto</span>
          </button>
          <Button variant="outline" size="lg" className="w-full" disabled={!catalog} onClick={() => fileRef.current?.click()}>
            <ImagePlus className="h-5 w-5" /> Subir imágenes
          </Button>
          <p className="text-center text-xs text-stone-400">Puedes elegir varias fotos a la vez. La IA hace el resto.</p>
        </>
      )}

      {items.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">Procesando productos</h2>
          {items.map((it) => (
            <Card key={it.key} className="flex items-center gap-3 p-3">
              <div className="h-16 w-16 shrink-0 overflow-hidden rounded-xl bg-stone-100">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                {(thumb(it.product) || it.preview) && <img src={it.state === "done" ? thumb(it.product) || it.preview : it.preview || thumb(it.product) || ""} alt="" className="h-full w-full object-cover" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold">{it.state === "done" && it.product?.name ? it.product.name : it.name}</div>
                <StateLabel it={it} />
              </div>
              {it.state === "error" && it.product && <Link href={`/products/${it.product.id}`} className="shrink-0 text-xs font-semibold text-accent underline">Completar manualmente</Link>}
              {it.state === "done" && <Check className="h-6 w-6 shrink-0 text-emerald-600" />}
              {it.state === "error" && !it.product && <X className="h-6 w-6 shrink-0 text-red-500" />}
            </Card>
          ))}
        </section>
      )}

      {items.length > 0 && pending === 0 && (
        <div className="sticky bottom-24 space-y-2 rounded-3xl bg-white p-4 shadow-2xl ring-1 ring-stone-200 md:bottom-4">
          <p className="text-center font-bold">{doneCount} {doneCount === 1 ? "producto detectado" : "productos detectados"}</p>
          <Link href={ids.length ? `/products/review?ids=${ids.join(",")}` : "/products/review"} className={cn(buttonVariants({ size: "xl" }), "w-full")}>REVISAR</Link>
        </div>
      )}
    </div>
  );
}

function StateLabel({ it }: { it: Item }) {
  if (it.state === "queued") return <span className="text-xs text-stone-500">En fila...</span>;
  if (it.state === "uploading") return <span className="flex items-center gap-1 text-xs text-stone-500"><Loader2 className="h-3 w-3 animate-spin" /> Subiendo</span>;
  if (it.state === "analyzing") return <span className="flex items-center gap-1 text-xs text-indigo-600"><Loader2 className="h-3 w-3 animate-spin" /> Analizando</span>;
  if (it.state === "done") return <span className="text-xs text-emerald-700">Listo</span>;
  return (
    <span className="flex items-start gap-1 text-xs text-red-600">
      <AlertCircle className="mt-0.5 h-3 w-3 shrink-0" />
      {it.product ? "No pudimos analizar automáticamente este producto. Puedes completar los datos manualmente." : it.message}
    </span>
  );
}
