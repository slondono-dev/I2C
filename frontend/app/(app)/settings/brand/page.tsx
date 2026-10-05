"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ImagePlus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { THEMES } from "@/components/catalog/themes";
import { THEME_LABEL, errMsg } from "@/lib/format";
import { cn } from "@/lib/utils";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/input";
import type { BrandModel, ThemeName } from "@/lib/types";

const HEX = /^#[0-9a-fA-F]{6}$/;

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <Label>{label}</Label>
      <div className="flex items-center gap-2">
        <input type="color" aria-label={label} value={HEX.test(value) ? value : "#000000"} onChange={(e) => onChange(e.target.value)} className="h-12 w-14 shrink-0 cursor-pointer rounded-xl border border-stone-300 bg-white p-1" />
        <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder="#4f46e5" maxLength={7} className={cn(value && !HEX.test(value) && "border-red-400")} />
      </div>
    </div>
  );
}

const SEL = "h-12 w-full rounded-xl border border-stone-300 bg-white px-3 text-sm";
const GENDERS = [["mujer", "Mujer"], ["hombre", "Hombre"], ["unisex", "Unisex"]];
const AGES = ["18-25", "25-35", "35-50"];
const STYLES = ["studio", "editorial", "street", "premium"];

function BrandModels({ brandId }: { brandId: string }) {
  const toast = useToast();
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [models, setModels] = useState<BrandModel[]>([]);
  const [f, setF] = useState({ name: "", gender: "unisex", age_range: "25-35", style: "studio", prompt: "" });
  const [saving, setSaving] = useState(false);
  const [del, setDel] = useState<BrandModel | null>(null);

  useEffect(() => { api.health().then((h) => setEnabled(!!h?.features.virtual_model)); }, []);
  useEffect(() => {
    if (!enabled) return;
    api.brandModels(brandId).then(setModels).catch((e) => toast(errMsg(e), "error"));
  }, [brandId, enabled, toast]);

  async function create() {
    if (!f.name.trim()) { toast("Escribe un nombre para el modelo", "error"); return; }
    setSaving(true);
    try {
      const m = await api.createBrandModel(brandId, { name: f.name.trim(), gender: f.gender, age_range: f.age_range, style: f.style, prompt_template: f.prompt.trim() || undefined });
      setModels((s) => [...s, m]); setF({ ...f, name: "", prompt: "" });
      toast("Modelo creado");
    } catch (e) { toast(errMsg(e), "error"); } finally { setSaving(false); }
  }
  async function remove() {
    if (!del) return;
    try { await api.deleteBrandModel(brandId, del.id); setModels((s) => s.filter((x) => x.id !== del.id)); toast("Modelo eliminado"); }
    catch (e) { toast(errMsg(e), "error"); } finally { setDel(null); }
  }

  if (enabled === null) return null;
  if (!enabled) return <p className="text-center text-sm text-stone-500">Función premium no activada</p>;
  return (
    <Card className="space-y-4">
      <div className="text-xs font-medium uppercase tracking-wide text-stone-500">Modelos de marca</div>
      {models.length === 0 ? <p className="text-sm text-stone-500">Aún no tienes modelos.</p> : (
        <ul className="space-y-2">
          {models.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-2 rounded-xl bg-stone-50 px-3 py-2">
              <div className="min-w-0"><div className="truncate font-semibold">{m.name}</div>
                <div className="text-xs text-stone-500">{[m.gender, m.age_range, m.style].filter(Boolean).join(" · ")}</div></div>
              <button aria-label={`Eliminar ${m.name}`} onClick={() => setDel(m)} className="rounded-xl p-2 text-red-600 hover:bg-stone-100"><Trash2 className="h-5 w-5" /></button>
            </li>
          ))}
        </ul>
      )}
      <div className="space-y-3 border-t border-stone-100 pt-3">
        <div><Label>Nombre</Label><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="Ej: Camila" /></div>
        <div className="grid grid-cols-3 gap-2">
          <div><Label>Género</Label><select className={SEL} value={f.gender} onChange={(e) => setF({ ...f, gender: e.target.value })}>{GENDERS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
          <div><Label>Edad</Label><select className={SEL} value={f.age_range} onChange={(e) => setF({ ...f, age_range: e.target.value })}>{AGES.map((a) => <option key={a}>{a}</option>)}</select></div>
          <div><Label>Estilo</Label><select className={SEL} value={f.style} onChange={(e) => setF({ ...f, style: e.target.value })}>{STYLES.map((a) => <option key={a}>{a}</option>)}</select></div>
        </div>
        <div><Label>Prompt personalizado (opcional)</Label>
          <Textarea value={f.prompt} onChange={(e) => setF({ ...f, prompt: e.target.value })} />
          <p className="mt-1 text-xs text-stone-500">Puedes usar los marcadores {"{style}"} y {"{gender}"}.</p></div>
        <Button className="w-full" disabled={saving} onClick={create}>{saving ? "Creando..." : "Crear modelo"}</Button>
      </div>
      <Dialog open={!!del} onClose={() => setDel(null)} title="¿Eliminar modelo?">
        <p className="mb-4 text-sm text-stone-600">Se eliminará &quot;{del?.name}&quot;. Esta acción no se puede deshacer.</p>
        <div className="flex gap-2"><Button variant="outline" className="flex-1" onClick={() => setDel(null)}>Cancelar</Button><Button variant="danger" className="flex-1" onClick={remove}>Eliminar</Button></div>
      </Dialog>
    </Card>
  );
}

export default function BrandSettings() {
  const { brand, loading, setBrands } = useWorkspace();
  const toast = useToast();
  const fileRef = useRef<HTMLInputElement>(null);
  const [f, setF] = useState({ name: "", whatsapp: "", primary: "", secondary: "", style: "minimal" as string });
  const [logo, setLogo] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!brand) return;
    setF({ name: brand.name, whatsapp: brand.whatsapp ?? "", primary: brand.primary_color ?? "", secondary: brand.secondary_color ?? "", style: brand.catalog_style ?? "minimal" });
    setLogo(brand.logo);
  }, [brand]);

  async function save() {
    if (!brand) return;
    if (!f.name.trim()) { toast("Escribe el nombre de tu marca", "error"); return; }
    if ((f.primary && !HEX.test(f.primary)) || (f.secondary && !HEX.test(f.secondary))) { toast("Usa colores en formato #RRGGBB", "error"); return; }
    setSaving(true);
    try {
      const b = await api.updateBrand(brand.id, { name: f.name.trim(), whatsapp: f.whatsapp.trim() || null, primary_color: f.primary || null, secondary_color: f.secondary || null, catalog_style: f.style });
      setBrands((s) => s.map((x) => (x.id === b.id ? b : x)));
      toast("Marca guardada");
    } catch (e) { toast(errMsg(e), "error"); } finally { setSaving(false); }
  }

  async function upload(file: File | undefined) {
    if (!brand || !file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) { toast("Usa una imagen JPG, PNG o WebP", "error"); return; }
    setUploading(true);
    try {
      const b = await api.uploadLogo(brand.id, file);
      setLogo(b.logo); setBrands((s) => s.map((x) => (x.id === b.id ? b : x)));
      toast("Logo actualizado");
    } catch (e) { toast(errMsg(e), "error"); } finally { setUploading(false); }
  }

  return (
    <div className="mx-auto max-w-md space-y-5 pb-8">
      <div className="flex items-center gap-3">
        <Link href="/more" aria-label="Volver" className="rounded-full p-2 hover:bg-stone-100"><ArrowLeft className="h-5 w-5" /></Link>
        <h1 className="text-2xl font-black">Ajustes de marca</h1>
      </div>
      {loading || !brand ? <Skeleton className="h-96" /> : (
        <>
          <Card className="space-y-3">
            <Label>Logo</Label>
            <div className="flex items-center gap-4">
              <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-stone-100">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                {logo ? <img src={logo} alt="Logo" className="h-full w-full object-contain" /> : <ImagePlus className="h-8 w-8 text-stone-400" />}
              </div>
              <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => { upload(e.target.files?.[0]); e.target.value = ""; }} />
              <Button variant="outline" disabled={uploading} onClick={() => fileRef.current?.click()}>{uploading ? "Subiendo..." : logo ? "Cambiar logo" : "Subir logo"}</Button>
            </div>
          </Card>
          <Card className="space-y-4">
            <div><Label>Nombre de la marca</Label><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
            <div><Label>WhatsApp</Label><Input type="tel" inputMode="tel" placeholder="573001234567" value={f.whatsapp} onChange={(e) => setF({ ...f, whatsapp: e.target.value })} /></div>
            <ColorField label="Color principal" value={f.primary} onChange={(v) => setF({ ...f, primary: v })} />
            <ColorField label="Color secundario" value={f.secondary} onChange={(v) => setF({ ...f, secondary: v })} />
          </Card>
          <Card>
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-stone-500">Estilo de catálogo</div>
            <div className="grid grid-cols-5 gap-2">
              {(Object.keys(THEMES) as ThemeName[]).map((k) => (
                <button key={k} onClick={() => setF({ ...f, style: k })} aria-pressed={f.style === k}
                  className={cn("rounded-xl border-2 py-3 text-center text-[10px] font-bold", f.style === k ? "border-accent" : "border-transparent")}
                  style={{ background: THEMES[k].bg, color: THEMES[k].accent === "#18181b" ? "#18181b" : THEMES[k].accent, fontFamily: THEMES[k].headingFont }}>
                  <div className="text-lg">Aa</div>{THEME_LABEL[k]}
                </button>
              ))}
            </div>
          </Card>
          <Button size="lg" className="w-full" disabled={saving} onClick={save}>{saving ? "Guardando..." : "Guardar cambios"}</Button>
          <BrandModels brandId={brand.id} />
        </>
      )}
    </div>
  );
}
