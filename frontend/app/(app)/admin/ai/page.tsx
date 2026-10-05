"use client";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { errMsg } from "@/lib/format";
import type { AIProvider, AIRouting, AIUsage } from "@/lib/types";

const TONE: Record<string, "green" | "amber" | "red" | "neutral"> = { healthy: "green", degraded: "amber", down: "red", quota_exceeded: "amber", disabled: "neutral" };
const LABEL: Record<string, string> = { healthy: "Activo", degraded: "Degradado", down: "Caído", quota_exceeded: "Cuota agotada", disabled: "Desactivado" };

export default function AdminAI() {
  const toast = useToast();
  const [providers, setProviders] = useState<AIProvider[] | null>(null);
  const [routing, setRouting] = useState<AIRouting[]>([]);
  const [usage, setUsage] = useState<AIUsage | null>(null);
  const [features, setFeatures] = useState<Record<string, boolean>>({});
  const [forbidden, setForbidden] = useState(false);

  const load = useCallback(async () => {
    try {
      const [p, r, u, f] = await Promise.all([api.aiProviders(), api.aiRouting(), api.aiUsage(24), api.aiFeatures()]);
      setProviders(p); setRouting(r); setUsage(u); setFeatures(f);
    } catch (e) { if (e instanceof ApiError && e.status === 403) setForbidden(true); else { toast(errMsg(e), "error"); setProviders([]); } }
  }, [toast]);
  useEffect(() => { load(); }, [load]);

  async function patch(name: string, b: { enabled?: boolean; priority?: number }) {
    try { setProviders(await api.patchProvider(name, b)); setRouting(await api.aiRouting()); } catch (e) { toast(errMsg(e), "error"); }
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
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Providers</h2>
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

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">Funciones</h2>
        <div className="flex flex-wrap gap-2">{Object.entries(features).map(([k, v]) => <Badge key={k} tone={v ? "green" : "neutral"}>{k.replace(/_/g, " ")}: {v ? "sí" : "no"}</Badge>)}</div>
      </section>
    </div>
  );
}
