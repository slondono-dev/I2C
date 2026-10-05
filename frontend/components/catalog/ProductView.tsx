"use client";
import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Share2, MessageCircle } from "lucide-react";
import type { PublicProduct } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import { THEMES } from "./themes";
import type { ThemeName } from "@/lib/types";

const LABEL: Record<string, string> = { original: "Original", clean: "Sin fondo", model: "Modelo", lifestyle: "Estilo", thumbnail: "Mini" };

export function productImages(p: PublicProduct): { key: string; url: string }[] {
  const out: { key: string; url: string }[] = [];
  const seen = new Set<string>();
  if (p.image) { out.push({ key: "main", url: p.image }); seen.add(p.image); }
  for (const [k, u] of Object.entries(p.images || {})) {
    if (u && !seen.has(u) && k !== "thumbnail") { out.push({ key: k, url: u }); seen.add(u); }
  }
  return out;
}

const isGif = (u: string) => /\.gif(\?|$)/i.test(u);

export function ProductView({ product, theme, shareUrl }: { product: PublicProduct; theme: ThemeName; shareUrl: string }) {
  const t = THEMES[theme];
  const imgs = useMemo(() => productImages(product), [product]);
  const [idx, setIdx] = useState(0);
  const [copied, setCopied] = useState(false);
  const cur = imgs[idx];
  const video = product.video;
  const [showVideo, setShowVideo] = useState(!!video);

  async function share() {
    const url = shareUrl.startsWith("http") ? shareUrl : window.location.origin + shareUrl;
    try {
      if (navigator.share) await navigator.share({ title: product.name, url });
      else { await navigator.clipboard.writeText(url); setCopied(true); setTimeout(() => setCopied(false), 2000); }
    } catch { /* cancelled */ }
  }

  return (
    <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-2">
      <div>
        <div className={`relative overflow-hidden ${t.aspect} ${t.imgClass}`} style={{ background: t.cardBg }}>
          {showVideo && video ? (isGif(video)
            /* eslint-disable-next-line @next/next/no-img-element */
            ? <img src={video} alt={product.name} className="absolute inset-0 h-full w-full object-cover" />
            : <video src={video} autoPlay muted loop playsInline className="absolute inset-0 h-full w-full object-cover" />) : (
          <AnimatePresence mode="wait">
            {cur && (
              <motion.img key={cur.url} src={cur.url} alt={product.name} className="absolute inset-0 h-full w-full object-cover"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.25 }} />
            )}
          </AnimatePresence>)}
        </div>
        {(imgs.length > 1 || (video && imgs.length > 0)) && (
          <div className="mt-3 flex gap-2">
            {video && (
              <button onClick={() => setShowVideo(true)} aria-label="Video" className="flex h-16 w-14 items-center justify-center rounded-md border-2 bg-black/5 text-xs font-bold" style={{ borderColor: showVideo ? "var(--accent)" : "transparent" }}>▶</button>
            )}
            {imgs.map((im, i) => (
              <button key={im.url} onClick={() => { setIdx(i); setShowVideo(false); }} aria-label={LABEL[im.key] || "Foto"}
                className="h-16 w-14 overflow-hidden rounded-md border-2" style={{ borderColor: !showVideo && i === idx ? "var(--accent)" : "transparent" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={im.url} alt="" loading="lazy" className="h-full w-full object-cover" />
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="flex flex-col gap-4">
        <div>
          {product.category && <div className="mb-1 text-xs uppercase tracking-widest" style={{ color: t.muted }}>{product.category}</div>}
          <h2 className="text-3xl font-semibold leading-tight" style={{ fontFamily: t.headingFont }}>{product.name}</h2>
          <div className="mt-2 text-2xl font-bold" style={{ color: "var(--accent)" }}>{formatPrice(product.price, product.currency)}</div>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: product.available ? "#22c55e" : "#ef4444" }} />
          <span>{product.available ? "Disponible" : "Agotado"}</span>
        </div>
        {product.color && <div className="text-sm"><span style={{ color: t.muted }}>Color: </span>{product.color}</div>}
        {product.sizes?.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span style={{ color: t.muted }}>Tallas:</span>
            {product.sizes.map((s) => (<span key={s} className="rounded-md border px-2.5 py-1 text-xs font-medium" style={{ borderColor: t.border }}>{s}</span>))}
          </div>
        )}
        {product.description && <p className="text-sm leading-relaxed" style={{ color: t.muted }}>{product.description}</p>}
        <div className="mt-2 space-y-3">
          {product.whatsapp_url && product.available && (
            <a href={product.whatsapp_url} target="_blank" rel="noopener noreferrer"
              className="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-[#25D366] text-base font-bold text-white shadow-lg active:scale-[0.98]">
              <MessageCircle className="h-5 w-5" /> PEDIR POR WHATSAPP
            </a>
          )}
          <button onClick={share} className="flex h-11 w-full items-center justify-center gap-2 rounded-2xl border text-sm font-medium" style={{ borderColor: t.border }}>
            <Share2 className="h-4 w-4" /> {copied ? "¡Link copiado!" : "Compartir"}
          </button>
        </div>
      </div>
    </div>
  );
}
