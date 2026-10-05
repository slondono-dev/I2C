"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ImagePlus } from "lucide-react";
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
import type { ThemeName } from "@/lib/types";

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
        </>
      )}
    </div>
  );
}
