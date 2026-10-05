"use client";
import { useWorkspace } from "@/hooks/useWorkspace";
import { CatalogCard } from "@/components/CatalogCard";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { THEMES } from "@/components/catalog/themes";
import { THEME_LABEL, errMsg } from "@/lib/format";
import { useToast } from "@/components/ui/toast";
import type { ThemeName } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function Catalogs() {
  const ws = useWorkspace();
  const toast = useToast();

  async function setTheme(id: string, theme: ThemeName) {
    try {
      const c = await api.updateCatalog(id, { theme });
      ws.setCatalogs((s) => s.map((x) => (x.id === id ? c : x)));
      toast("Estilo actualizado");
    } catch (e) { toast(errMsg(e), "error"); }
  }

  return (
    <div className="mx-auto max-w-md space-y-5">
      <h1 className="text-2xl font-black">Catálogos</h1>
      {ws.loading ? <Skeleton className="h-64" /> : ws.catalogs.map((c) => (
        <div key={c.id} className="space-y-3">
          <CatalogCard catalog={c} onChange={(n) => ws.setCatalogs((s) => s.map((x) => (x.id === n.id ? n : x)))} />
          <Card>
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-stone-500">Estilo del catálogo</div>
            <div className="grid grid-cols-5 gap-2">
              {(Object.keys(THEMES) as ThemeName[]).map((k) => (
                <button key={k} onClick={() => setTheme(c.id, k)} aria-pressed={c.theme === k}
                  className={cn("rounded-xl border-2 py-3 text-center text-[10px] font-bold", c.theme === k ? "border-accent" : "border-transparent")}
                  style={{ background: THEMES[k].bg, color: THEMES[k].accent === "#18181b" ? "#18181b" : THEMES[k].accent, fontFamily: THEMES[k].headingFont }}>
                  <div className="text-lg">Aa</div>{THEME_LABEL[k]}
                </button>
              ))}
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
}
