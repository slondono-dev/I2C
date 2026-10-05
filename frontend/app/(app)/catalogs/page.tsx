"use client";
import { useState } from "react";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
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

  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newTheme, setNewTheme] = useState<ThemeName>("minimal");
  const [renaming, setRenaming] = useState<{ id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState<{ id: string; name: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function create() {
    if (!ws.brand || !newName.trim()) { toast("Escribe un nombre", "error"); return; }
    setBusy(true);
    try {
      const c = await api.createCatalog({ brand_id: ws.brand.id, name: newName.trim(), theme: newTheme });
      ws.setCatalogs((s) => [...s, c]); setCreating(false); setNewName(""); toast("Catálogo creado");
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }
  async function rename() {
    if (!renaming || !renaming.name.trim()) return;
    setBusy(true);
    try {
      const c = await api.updateCatalog(renaming.id, { name: renaming.name.trim() });
      ws.setCatalogs((s) => s.map((x) => (x.id === c.id ? c : x))); setRenaming(null); toast("Nombre actualizado");
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }
  async function remove() {
    if (!deleting) return;
    setBusy(true);
    try {
      await api.deleteCatalog(deleting.id);
      ws.setCatalogs((s) => s.filter((x) => x.id !== deleting.id)); setDeleting(null); toast("Catálogo eliminado");
    } catch (e) { toast(errMsg(e), "error"); } finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-md space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-black">Catálogos</h1>
        <Button size="sm" onClick={() => setCreating(true)} disabled={!ws.brand}><Plus className="h-4 w-4" />Nuevo catálogo</Button>
      </div>
      {ws.loading ? <Skeleton className="h-64" /> : ws.catalogs.map((c) => (
        <div key={c.id} className="space-y-3">
          <CatalogCard catalog={c} onChange={(n) => ws.setCatalogs((s) => s.map((x) => (x.id === n.id ? n : x)))} />
          <div className="flex gap-2">
            <Button size="sm" variant="outline" className="flex-1" onClick={() => setRenaming({ id: c.id, name: c.name })}><Pencil className="h-4 w-4" />Renombrar</Button>
            <Button size="sm" variant="outline" className="flex-1 text-red-600" onClick={() => setDeleting({ id: c.id, name: c.name })}><Trash2 className="h-4 w-4" />Eliminar</Button>
          </div>
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
      <Dialog open={creating} onClose={() => setCreating(false)} title="Nuevo catálogo">
        <div className="space-y-3">
          <div><Label>Nombre</Label><Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Colección verano" /></div>
          <div className="grid grid-cols-5 gap-2">
            {(Object.keys(THEMES) as ThemeName[]).map((k) => (
              <button key={k} onClick={() => setNewTheme(k)} aria-pressed={newTheme === k}
                className={cn("rounded-xl border-2 py-2 text-center text-[10px] font-bold", newTheme === k ? "border-accent" : "border-transparent")}
                style={{ background: THEMES[k].bg, color: THEMES[k].accent === "#18181b" ? "#18181b" : THEMES[k].accent, fontFamily: THEMES[k].headingFont }}>
                <div className="text-lg">Aa</div>{THEME_LABEL[k]}
              </button>
            ))}
          </div>
          <Button className="w-full" disabled={busy} onClick={create}>{busy ? "Creando..." : "Crear catálogo"}</Button>
        </div>
      </Dialog>
      <Dialog open={!!renaming} onClose={() => setRenaming(null)} title="Renombrar catálogo">
        <div className="space-y-3">
          <Input value={renaming?.name ?? ""} onChange={(e) => setRenaming((r) => (r ? { ...r, name: e.target.value } : r))} />
          <Button className="w-full" disabled={busy} onClick={rename}>Guardar</Button>
        </div>
      </Dialog>
      <Dialog open={!!deleting} onClose={() => setDeleting(null)} title="¿Eliminar catálogo?">
        <p className="mb-4 text-sm text-stone-600">Se eliminará «{deleting?.name}» con sus productos. Esta acción no se puede deshacer.</p>
        <div className="flex gap-2"><Button variant="outline" className="flex-1" onClick={() => setDeleting(null)}>Cancelar</Button><Button variant="danger" className="flex-1" disabled={busy} onClick={remove}>Eliminar</Button></div>
      </Dialog>
    </div>
  );
}
