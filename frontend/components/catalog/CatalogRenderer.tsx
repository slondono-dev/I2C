"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { X, ShoppingBag } from "lucide-react";
import type { PublicCatalog, PublicProduct, ThemeName } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import { THEMES } from "./themes";
import { ProductView, productImages } from "./ProductView";

type Props = {
  catalog: Pick<PublicCatalog, "name" | "slug" | "description" | "brand">;
  products: PublicProduct[];
  theme: ThemeName;
  basePath?: string; // e.g. /c/slug ; used for share URLs
  banner?: React.ReactNode;
};

export function themeStyle(theme: ThemeName, primary?: string | null): React.CSSProperties {
  const t = THEMES[theme] ?? THEMES.minimal;
  return {
    "--accent": primary || t.accent, "--bg": t.bg, "--fg": t.fg, "--muted": t.muted, "--cardBg": t.cardBg, "--border": t.border,
    background: t.bg, color: t.fg, fontFamily: t.font,
  } as React.CSSProperties;
}

export function CatalogRenderer({ catalog, products, theme, basePath, banner }: Props) {
  const t = THEMES[theme] ?? THEMES.minimal;
  const [cat, setCat] = useState<string>("Todo");
  const [open, setOpen] = useState<PublicProduct | null>(null);
  const categories = useMemo(() => ["Todo", ...Array.from(new Set(products.map((p) => p.category).filter(Boolean) as string[]))], [products]);
  const shown = cat === "Todo" ? products : products.filter((p) => p.category === cat);
  const base = basePath ?? `/c/${catalog.slug}`;
  const brand = catalog.brand;

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  return (
    <div className="min-h-screen" style={themeStyle(theme, brand.primary_color)}>
      {banner}
      <header className="sticky top-0 z-20 border-b backdrop-blur" style={{ borderColor: t.border, background: `${t.bg}ee` }}>
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          {brand.logo && /* eslint-disable-next-line @next/next/no-img-element */ <img src={brand.logo} alt="" className="h-8 w-8 rounded-full object-cover" />}
          <span className={t.brandClass} style={{ fontFamily: t.headingFont }}>{brand.name}</span>
          <ShoppingBag className="ml-auto h-5 w-5 opacity-60" aria-hidden />
        </div>
      </header>

      <section className={`mx-auto max-w-6xl px-4 pb-6 pt-10 ${t.headerAlign}`}>
        <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
          className={t.headingClass} style={{ fontFamily: t.headingFont }}>{catalog.name}</motion.h1>
        {catalog.description && <p className="mx-auto mt-3 max-w-xl text-sm" style={{ color: t.muted }}>{catalog.description}</p>}
        {categories.length > 2 && (
          <div className={`mt-6 flex gap-2 overflow-x-auto pb-1 ${t.headerAlign === "text-center" ? "justify-center" : ""}`}>
            {categories.map((c) => (
              <button key={c} onClick={() => setCat(c)} className="shrink-0 rounded-full border px-4 py-1.5 text-xs font-medium transition"
                style={c === cat ? { background: "var(--accent)", color: t.bg, borderColor: "var(--accent)" } : { borderColor: t.border }}>
                {c}
              </button>
            ))}
          </div>
        )}
      </section>

      <main className="mx-auto max-w-6xl px-4 pb-24">
        {shown.length === 0 ? (
          <p className="py-20 text-center text-sm" style={{ color: t.muted }}>Pronto habrá productos aquí.</p>
        ) : (
          <div className={`grid ${t.gridClass}`}>
            {shown.map((p, i) => <ProductCard key={p.id} p={p} i={i} theme={theme} onOpen={() => setOpen(p)} />)}
          </div>
        )}
      </main>

      <footer className="pb-10 text-center text-xs" style={{ color: t.muted }}>
        Catálogo creado con <Link href="/" className="underline">I2C</Link>
      </footer>

      <AnimatePresence>
        {open && (
          <motion.div className="fixed inset-0 z-40 flex items-end justify-center bg-black/60 md:items-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(null)}>
            <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 80, opacity: 0 }} transition={{ type: "spring", damping: 28, stiffness: 260 }}
              className="relative max-h-[94vh] w-full overflow-y-auto rounded-t-3xl p-5 pb-8 md:max-w-4xl md:rounded-3xl"
              style={{ ...themeStyle(theme, brand.primary_color) }} onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
              <button onClick={() => setOpen(null)} aria-label="Cerrar" className="absolute right-3 top-3 z-10 rounded-full bg-black/40 p-2 text-white"><X className="h-5 w-5" /></button>
              <ProductView product={open} theme={theme} shareUrl={`${base}/p/${open.id}`} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ProductCard({ p, i, theme, onOpen }: { p: PublicProduct; i: number; theme: ThemeName; onOpen: () => void }) {
  const t = THEMES[theme];
  const imgs = productImages(p);
  const [hover, setHover] = useState(false);
  const alt = imgs[1];
  const src = (hover && alt ? alt.url : imgs[0]?.url) || null;
  const small = src && src === p.image && p.image_small ? p.image_small : null;
  return (
    <motion.article initial={{ opacity: 0, y: 24, scale: 0.97 }} whileInView={{ opacity: 1, y: 0, scale: 1 }} viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, delay: Math.min(i % 4, 3) * t.stagger }} className={`group cursor-pointer ${t.cardClass}`}
      onClick={onOpen} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} role="button" tabIndex={0}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onOpen()}>
      <div className={`relative overflow-hidden ${t.aspect} ${t.imgClass}`} style={{ background: t.cardBg }}>
        <AnimatePresence initial={false}>
          {src && (
            <motion.img key={src} src={small ?? src} srcSet={small && p.image ? `${small} 480w, ${p.image} 1200w` : undefined} sizes="(max-width: 640px) 50vw, 33vw" alt={p.name} loading="lazy" className="absolute inset-0 h-full w-full object-cover"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }} whileHover={{ scale: t.hover }} />
          )}
        </AnimatePresence>
        {!p.available && <span className="absolute left-2 top-2 rounded-full bg-black/70 px-2.5 py-1 text-[10px] font-bold uppercase text-white">Agotado</span>}
      </div>
      <div className="mt-3 flex items-baseline justify-between gap-2 px-1">
        <h3 className={`${t.nameClass} line-clamp-2`} style={{ fontFamily: t.headingFont }}>{p.name}</h3>
        <span className={`shrink-0 ${t.priceClass}`}>{formatPrice(p.price, p.currency)}</span>
      </div>
    </motion.article>
  );
}
