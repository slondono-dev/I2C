"use client";
import { useState } from "react";
import { CatalogRenderer } from "@/components/catalog/CatalogRenderer";
import { demoCatalog } from "@/lib/demo-data";
import { THEME_LABEL } from "@/lib/format";
import type { ThemeName } from "@/lib/types";

const names = Object.keys(THEME_LABEL) as ThemeName[];

export default function Demo() {
  const [theme, setTheme] = useState<ThemeName>("editorial");
  const c = demoCatalog(theme);
  return (
    <CatalogRenderer catalog={c} products={c.products} theme={theme} basePath="/demo"
      banner={
        <div className="sticky top-0 z-30 flex items-center gap-2 overflow-x-auto bg-black px-3 py-2 text-xs text-white">
          <span className="shrink-0 opacity-70">Estilo:</span>
          {names.map((n) => (
            <button key={n} onClick={() => setTheme(n)} className={`shrink-0 rounded-full px-3 py-1 font-semibold ${n === theme ? "bg-white text-black" : "bg-white/15"}`}>{THEME_LABEL[n]}</button>
          ))}
        </div>
      } />
  );
}
