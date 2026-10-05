"use client";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { errMsg } from "@/lib/format";
import { Button } from "@/components/ui/button";
import type { ExperimentResult, ExperimentTask, AIMetrics, AIProvider, AIRouting, AIUsage } from "@/lib/types";

const TONE: Record<string, "green" | "amber" | "red" | "neutral"> = { healthy: "green", degraded: "amber", down: "red", quota_exceeded: "amber", disabled: "neutral" };
const LABEL: Record<string, string> = { healthy: "Activo", degraded: "Degradado", down: "Caído", quota_exceeded: "Cuota agotada", disabled: "Desactivado" };

const TASKS: [ExperimentTask, string][] = [["product_name", "Nombre de producto"], ["product_description", "Descripción"], ["product_recognition", "Reconocimiento"], ["background_removal", "Quitar fondo"], ["virtual_model", "Modelo virtual"]];

function Experiments({ providers }: { providers: AIProvider[] }) {
  const toast = useToast();
  const [task, setTask] = useState<ExperimentTask>("product_name");
  const [sel, setSel] = useState<string[]>([]);
  const [productId, setProductId] = useState("");
  const [category, setCategory] = useState("");
  const [color, setColor] = useState("");
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<ExperimentResult[] | null>(null);
  const textTask = task === "product_name" || task === "product_description";

  const toggle = (n: string) => setSel((s) => (s.includes(n) ? s.filter((x) => x !== n) : s.length >= 6 ? s : [...s, n]));
  async function run() {
    if (sel.length === 0) { toast("Elige al menos un provider", "error"); return; }
    setRunning(true); setResults(null);
    try {
      const r = await api.aiExperiment({
        task, providers: sel, product_id: productId.trim() || undefined,
        payload: textTask ? { attributes: { category: category.trim(), color: color.trim() } } : undefined,
      });
      setResults(r.results);
    } catch (e) { toast(errMsg(e), "error"); } finally { setRunning(false); }
  }
  const out = (d: unknown) => (d == null ? "—" : typeof d === "string" ? d : JSON.stringify(d, null, 1));

  return (
    <section>
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Experimentos</h2>
      <Card className="space-y-3">
        <div><label className="mb-1 block text-sm font-medium">Tarea</label>
          <select value={task} onChange={(e) => setTask(e.target.value as ExperimentTask)} className="h-11 w-full rounded-xl border border-stone-300 bg-white px-3 text-sm">
            {TASKS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          {providers.map((p) => (
            <label key={p.name} className="flex items-center gap-2 text-sm"><input type="checkbox" className="h-5 w-5 accent-indigo-600" checked={sel.includes(p.name)} onChange={() => toggle(p.name)} />{p.display_name}</label>
          ))}
        </div>
        <Input placeholder="ID de producto (para tareas con imagen)" value={productId} onChange={(e) => setProductId(e.target.value)} className="h-11" />
        {textTask && <div className="grid grid-cols-2 gap-2">
          <Input placeholder="Categoría" value={category} onChange={(e) => setCategory(e.target.value)} className="h-11" />
          <Input placeholder="Color" value={color} onChange={(e) => setColor(e.target.value)} className="h-11" /></div>}
        <Button className="w-full" disabled={running} onClick={run}>{running ? "Comparando..." : "Comparar"}</Button>
      </Card>
      {results && (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {results.map((r, i) => (
            <Card key={`${r.provider}-${i}`} className="space-y-2 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="font-bold">{r.provider}{r.model ? <span className="ml-1 text-xs font-normal text-stone-500">{r.model}</span> : null}</div>
                <Badge tone={r.success ? "green" : "red"}>{r.success ? "✓ Éxito" : "✗ Falló"}</Badge>
              </div>
              <div className="flex gap-4 text-xs text-stone-500">
                <span>{r.latency_ms != null ? `${Math.round(r.latency_ms)} ms` : "—"}</span>
                <span>{r.cost != null ? `$${Number(r.cost).toFixed(4)}` : "—"}</span>
              </div>
              {r.error && <p className="text-xs text-red-700">{r.error}</p>}
              <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-stone-50 p-2 text-xs">{out(r.data)}</pre>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

export default function AdminAI() {
  const toast = useToast();
  const [providers, setProviders] = useState<AIProvider[] | null>(null);
  const [routing, setRouting] = useState<AIRouting[]>([]);
  const [usage, setUsage] = useState<AIUsage | null>(null);
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [metrics, setMetrics] = useState<AIMetrics | null>(null);
  const [checking, setChecking] = useState(false);
  const [forbidden, setForbidden] = useState(false);

  const load = useCallback(async () => {
    try {
      const [p, r, u, f] = await Promise.all([api.aiProviders(), api.aiRouting(), api.aiUsage(24), api.aiFeatures()]);
      setProviders(p); setRouting(r); setUsage(u); setFeatures({ ...f });
      api.aiMetrics(168).then(setMetrics).catch(() => setMetrics(null));
    } catch (e) { if (e instanceof ApiError && e.status === 403) setForbidden(true); else { toast(errMsg(e), "error"); setProviders([]); } }
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  async function patch(name: string, b: { enabled?: boolean; priority?: number }) {
    try { setProviders(await api.patchProvider(name, b)); setRouting(await api.aiRouting()); } catch (e) { toast(errMsg(e), "error"); }
  }

  async function healthCheck() {
    setChecking(true);
    try { await api.aiHealthCheck(); setProviders(await api.aiProviders()); toast("Salud revisada"); }
    catch (e) { toast(errMsg(e), "error"); } finally { setChecking(false); }
  }

  if (forbidden) return <Card className="mx-auto max-w-md py-10 text-center font-semibold">Solo administradores</Card>;
  const act = typeof usage?.active_providers === "number" ? usage.active_providers : Array.isArray(usage?.active_providers) ? usage.active_providers.length : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-black">Panel de IA</h1>
      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">IA hoy</h2>
        {!usage ? <Skeleton className="h-24" /> : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            {[["Solicitudes", usage.requests], ["Costo", `$${Number(usage.cost).toFixed(2)}`], ["% gratuitas", `${Math.round(usage.free_ratio * (usage.free_ratio <= 1 ? 100 : 1))}%`], ["Fallbacks", usage.fallbacks], ["Providers activos", act]].map(([l, v]) => (
              <Card key={String(l)} className="p-3 text-center"><div className="text-2xl font-black">{v}</div><div className="text-xs text-stone-500">{l}</div></Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Métricas (últimos 7 días)</h2>
        {!metrics ? <Skeleton className="h-24" /> : (() => {
          const sec = (v: number | null) => (v == null ? "—" : v >= 60 ? `${(v / 60).toFixed(1)} min` : `${v.toFixed(1)} s`);
          const pct = (v: number | null) => (v == null ? "—" : `${Math.round(v * 100)}%`);
          const usd = (v: number | null) => (v == null ? "—" : `$${v.toFixed(3)}`);
          const rows: [string, string | number][] = [
            ["Foto → producto", sec(metrics.photo_to_product_seconds_avg)], ["Producto → catálogo", sec(metrics.product_to_catalog_seconds_avg)],
            ["Costo por producto", usd(metrics.ai_cost_per_product)], ["% gratuitas", pct(metrics.free_provider_ratio)],
            ["Fallbacks", pct(metrics.fallback_rate)], ["Errores", pct(metrics.ai_error_rate)],
            ["Procesados", metrics.products_processed], ["Publicados", metrics.products_published],
          ];
          return <div className="grid grid-cols-2 gap-3 md:grid-cols-4">{rows.map(([l, v]) => (
            <Card key={l} className="p-3 text-center"><div className="text-2xl font-black">{v}</div><div className="text-xs text-stone-500">{l}</div></Card>
          ))}</div>;
        })()}
      </section>

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">Providers</h2>
          <Button size="sm" variant="outline" disabled={checking} onClick={healthCheck}>{checking ? "Revisando..." : "Revisar salud ahora"}</Button>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {providers === null && [0, 1].map((i) => <Skeleton key={i} className="h-36" />)}
          {providers?.map((p) => (
            <Card key={p.name} className="space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div><div className="font-bold">{p.display_name}</div><div className="text-xs text-stone-500">{p.capabilities.join(" · ")}</div></div>
                <Badge tone={TONE[p.status]}>{LABEL[p.status] ?? p.status}</Badge>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-xs text-stone-500">
                <div><b className="block text-base text-stone-900">{p.success_rate != null ? `${Math.round(p.success_rate * (p.success_rate <= 1 ? 100 : 1))}%` : "—"}</b>éxito</div>
                <div><b className="block text-base text-stone-900">{p.avg_latency_ms != null ? `${Math.round(p.avg_latency_ms)}ms` : "—"}</b>latencia</div>
                <div><b className="block text-base text-stone-900">{p.consecutive_failures}</b>fallos</div>
              </div>
              {!p.configured && <p className="text-xs text-amber-700">Sin configurar (falta API key)</p>}
              <div className="flex items-center justify-between gap-3">
                <label className="flex items-center gap-2 text-sm font-medium"><input type="checkbox" className="h-5 w-5 accent-indigo-600" checked={p.enabled} onChange={(e) => patch(p.name, { enabled: e.target.checked })} /> Activado</label>
                <label className="flex items-center gap-2 text-sm">Prioridad
                  <Input type="number" defaultValue={p.priority} key={p.priority} className="h-9 w-20" onBlur={(e) => { const v = parseInt(e.target.value, 10); if (!Number.isNaN(v) && v !== p.priority) patch(p.name, { priority: v }); }} /></label>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Ruteo por tarea</h2>
        <Card className="overflow-x-auto p-0">
          <table className="w-full text-sm"><thead className="bg-stone-50 text-left text-xs uppercase text-stone-500"><tr><th className="p-3">Tarea</th><th>Orden</th><th>Activo</th></tr></thead>
            <tbody>{routing.map((r) => (<tr key={r.task} className="border-t border-stone-100"><td className="p-3 font-medium">{r.task}</td><td>{r.providers.join(" → ")}</td><td>{r.active ? <Badge tone="green">{r.active}</Badge> : "—"}</td></tr>))}</tbody></table>
        </Card>
      </section>

      {providers && providers.length > 0 && <Experiments providers={providers} />}

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Funciones</h2>
        <div className="flex flex-wrap gap-2">{Object.entries(features).map(([k, v]) => <Badge key={k} tone={v ? "green" : "neutral"}>{k.replace(/_/g, " ")}: {v ? "sí" : "no"}</Badge>)}</div>
      </section>
    </div>
  );
}
