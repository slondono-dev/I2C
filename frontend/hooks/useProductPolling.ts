"use client";
import { useEffect, useRef } from "react";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";

/** Polls products that are 'processing' every 1.5s and reports updates. Stops per-item after maxMs. */
export function useProductPolling(products: Product[], onUpdate: (p: Product) => void, maxMs = 90000) {
  const started = useRef<Record<string, number>>({});
  const cb = useRef(onUpdate);
  cb.current = onUpdate;
  const ids = products.filter((p) => p.status === "processing").map((p) => p.id).sort().join(",");
  useEffect(() => {
    if (!ids) return;
    const t = setInterval(async () => {
      for (const id of ids.split(",")) {
        started.current[id] ??= Date.now();
        if (Date.now() - started.current[id] > maxMs) continue;
        try { const p = await api.product(id); if (p.status !== "processing") cb.current(p); } catch { /* retry */ }
      }
    }, 1500);
    return () => clearInterval(t);
  }, [ids, maxMs]);
}
