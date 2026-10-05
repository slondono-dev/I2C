"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { errMsg, cleanPhone } from "@/lib/format";
import { useAuthGuard } from "@/hooks/useAuthGuard";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { THEMES } from "@/components/catalog/themes";
import type { ThemeName } from "@/lib/types";
import { cn } from "@/lib/utils";

const SWATCH: Record<ThemeName, { bg: string; fg: string; font: string; label: string }> = {
  minimal: { bg: "#ffffff", fg: "#18181b", font: "ui-sans-serif", label: "Minimal" },
  editorial: { bg: "#f5efe6", fg: "#2b2118", font: "Georgia, serif", label: "Editorial" },
  street: { bg: "#0a0a0a", fg: "#e5ff3d", font: "Impact, sans-serif", label: "Street" },
  premium: { bg: "#14110f", fg: "#d4af37", font: "Georgia, serif", label: "Premium" },
  colorful: { bg: "#ffe3f1", fg: "#7c3aed", font: "ui-rounded, system-ui", label: "Colorido" },
};

export default function Onboarding() {
  const router = useRouter();
  const { ready } = useAuthGuard();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+57 ");
  const [style, setStyle] = useState<ThemeName>("minimal");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await api.createBrand({ name, whatsapp: cleanPhone(phone) || undefined, catalog_style: style, primary_color: THEMES[style].accent });
      // make the default catalog follow the chosen style
      const [b] = await api.brands();
      const cats = b ? await api.catalogs(b.id) : [];
      if (cats[0]) await api.updateCatalog(cats[0].id, { theme: style }).catch(() => {});
      router.replace("/dashboard");
    } catch (err) { setError(errMsg(err)); } finally { setBusy(false); }
  }
  if (!ready) return null;

  return (
    <main className="mx-auto min-h-screen max-w-md px-6 py-10">
      <h1 className="text-3xl font-black tracking-tight">Crea tu marca</h1>
      <p className="mt-1 text-stone-500">Solo dos datos y listo.</p>
      <form onSubmit={submit} className="mt-6 space-y-5">
        <div><Label>Nombre de tu marca</Label><Input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Ej: Moda Luna" /></div>
        <div><Label>WhatsApp (con código de país)</Label><Input type="tel" inputMode="tel" value={phone} onChange={(e) => setPhone(e.target.value)} required placeholder="+57 300 123 4567" />
          <p className="mt-1 text-xs text-stone-400">Aquí recibirás los pedidos.</p></div>
        <div>
          <Label>Estilo de tu catálogo</Label>
          <div className="grid grid-cols-3 gap-3">
            {(Object.keys(SWATCH) as ThemeName[]).map((k) => (
              <button type="button" key={k} onClick={() => setStyle(k)} aria-pressed={style === k}
                className={cn("rounded-2xl border-2 p-3 text-center transition", style === k ? "border-accent ring-2 ring-accent/20" : "border-stone-200")}
                style={{ background: SWATCH[k].bg, color: SWATCH[k].fg, fontFamily: SWATCH[k].font }}>
                <div className="text-2xl font-bold">Aa</div>
                <div className="text-[11px] font-semibold">{SWATCH[k].label}</div>
              </button>
            ))}
          </div>
        </div>
        {error && <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
        <Button size="xl" className="w-full" disabled={busy || !name}>{busy ? "Creando..." : "Continuar"}</Button>
      </form>
    </main>
  );
}
