import type { PublicCatalog, PublicProduct } from "./types";

function svg(c1: string, c2: string, shape: "tee" | "pants" | "bag" | "shoe", accent = "#ffffff"): string {
  const shapes = {
    tee: `<path d="M180 180 L260 150 Q300 190 340 150 L420 180 L460 260 L410 285 L390 255 L390 520 L210 520 L210 255 L190 285 L140 260 Z" fill="${accent}" fill-opacity=".9"/>`,
    pants: `<path d="M220 150 L380 150 L400 520 L320 520 L300 290 L280 520 L200 520 Z" fill="${accent}" fill-opacity=".9"/>`,
    bag: `<rect x="190" y="270" width="220" height="210" rx="22" fill="${accent}" fill-opacity=".9"/><path d="M240 270 Q240 190 300 190 Q360 190 360 270" stroke="${accent}" stroke-width="16" fill="none"/>`,
    shoe: `<path d="M150 400 Q150 300 230 290 L300 360 L420 380 Q470 390 470 430 L470 460 L150 460 Z" fill="${accent}" fill-opacity=".9"/>`,
  };
  const out = `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="800" viewBox="0 0 600 800"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient></defs><rect width="600" height="800" fill="url(#g)"/><g transform="translate(0 60)">${shapes[shape]}</g></svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(out)}`;
}

type Seed = [string, string, number, string, string, string[], string, "tee" | "pants" | "bag" | "shoe", string, string, string];
const seeds: Seed[] = [
  ["Camiseta Oversize Arena", "Algodón pesado, corte relajado y caída perfecta.", 79900, "Camisetas", "Arena", ["S", "M", "L"], "#e9d5b5", "tee", "#c9a77c", "#f3e6cf", "#8c6a3f"],
  ["Jogger Cargo Negro", "Bolsillos laterales y puño ajustable.", 139900, "Pantalones", "Negro", ["M", "L", "XL"], "#27272a", "pants", "#52525b", "#18181b", "#e4e4e7"],
  ["Bolso Mini Terracota", "Cuero vegano con correa ajustable.", 99900, "Accesorios", "Terracota", [], "#c2603f", "bag", "#e08a5f", "#a44a2c", "#fff1e6"],
  ["Tenis Cloud Blanco", "Suela ligera, amortiguación todo el día.", 249900, "Calzado", "Blanco", ["38", "40", "42"], "#cbd5e1", "shoe", "#e2e8f0", "#94a3b8", "#ffffff"],
  ["Camiseta Gráfica Lima", "Estampado frontal en serigrafía.", 69900, "Camisetas", "Lima", ["S", "M"], "#bef264", "tee", "#a3e635", "#d9f99d", "#365314"],
  ["Pantalón Lino Verde", "Fresco, ligero y elegante.", 159900, "Pantalones", "Verde", ["S", "M", "L"], "#4d7c5a", "pants", "#6aa07a", "#2f5a3c", "#ecfdf5"],
  ["Tote Bag Lienzo", "Capacidad para todo tu día.", 59900, "Accesorios", "Crudo", [], "#f1e9da", "bag", "#fbf6ea", "#e0d3b8", "#7a6a4a"],
  ["Tenis Retro Rosa", "Inspiración noventera, comodidad real.", 219900, "Calzado", "Rosa", ["37", "39"], "#f9a8d4", "shoe", "#fbcfe8", "#ec4899", "#ffffff"],
];

export const demoProducts: PublicProduct[] = seeds.map((s, i) => {
  const main = svg(s[8], s[9], s[7], s[10]);
  const alt = svg(s[9], s[8], s[7], s[10]);
  return {
    id: `demo-${i + 1}`, sku: `DEMO-${i + 1}`, name: s[0], description: s[1], price: s[2], currency: "COP",
    available: i !== 6, stock: i === 6 ? 0 : 10, category: s[3], color: s[4], sizes: s[5],
    image: main, images: { clean: alt }, whatsapp_url: "https://wa.me/573001234567?text=Hola%2C%20me%20interesa%20" + encodeURIComponent(s[0]),
  };
});

export function demoCatalog(theme: PublicCatalog["theme"]): PublicCatalog {
  return {
    name: "Colección Primavera", slug: "demo", description: "Un vistazo a cómo se verá tu catálogo.", theme,
    brand: { name: "Moda Luna", slug: "moda-luna", logo: null, whatsapp: "573001234567", primary_color: null, secondary_color: null, font: null },
    products: demoProducts, public_url: "/demo", qr_url: "",
  };
}
