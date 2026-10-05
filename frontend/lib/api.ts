import { clearSession, getToken } from "./auth";
import type * as T from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
const BASE = `${API_URL}/api/v1`;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

function detailToString(d: unknown): string {
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => (x && typeof x === "object" && "msg" in x ? String((x as { msg: unknown }).msg) : String(x))).join(", ");
  return "Solicitud inválida";
}

async function raw(path: string, init: RequestInit = {}, auth = true): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (auth && token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  let res: Response;
  try { res = await fetch(`${BASE}${path}`, { ...init, headers }); }
  catch { throw new ApiError(0, "No pudimos conectar con el servidor. Revisa tu conexión."); }
  if (res.status === 401 && auth && typeof window !== "undefined" && !path.startsWith("/auth/login") && !path.startsWith("/auth/register")) {
    clearSession();
    window.location.href = "/login";
    throw new ApiError(401, "Sesión expirada");
  }
  if (!res.ok) {
    let msg = `Error ${res.status}`;
    try { const j = await res.json(); msg = detailToString(j?.detail ?? j); } catch { /* ignore */ }
    throw new ApiError(res.status, msg);
  }
  return res;
}

async function req<R>(path: string, init: RequestInit = {}, auth = true): Promise<R> {
  const res = await raw(path, init, auth);
  if (res.status === 204) return undefined as R;
  return (await res.json()) as R;
}
const json = (method: string, body?: unknown): RequestInit => ({ method, body: body === undefined ? undefined : JSON.stringify(body) });
const qs = (o: Record<string, string | number | boolean | undefined | null>) => {
  const p = new URLSearchParams();
  Object.entries(o).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== "") p.set(k, String(v)); });
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const api = {
  register: (b: { name: string; email: string; password: string }) => req<T.AuthResponse>("/auth/register", json("POST", b), false),
  login: (b: { email: string; password: string }) => req<T.AuthResponse>("/auth/login", json("POST", b), false),
  me: () => req<T.User>("/auth/me"),

  brands: () => req<T.Brand[]>("/brands"),
  createBrand: (b: Partial<T.Brand> & { name: string }) => req<T.Brand>("/brands", json("POST", b)),
  updateBrand: (id: string, b: Partial<T.Brand>) => req<T.Brand>(`/brands/${id}`, json("PATCH", b)),

  uploadLogo: (id: string, file: File) => {
    const fd = new FormData(); fd.append("file", file);
    return req<T.Brand>(`/brands/${id}/logo`, { method: "POST", body: fd });
  },

  catalogs: (brand_id?: string) => req<T.Catalog[]>(`/catalogs${qs({ brand_id })}`),
  createCatalog: (b: { brand_id: string; name: string; theme: T.ThemeName; slug?: string; description?: string }) =>
    req<T.Catalog>("/catalogs", json("POST", b)),
  deleteCatalog: (id: string) => req<void>(`/catalogs/${id}`, json("DELETE")),
  updateCatalog: (id: string, b: Partial<T.Catalog>) => req<T.Catalog>(`/catalogs/${id}`, json("PATCH", b)),
  publishCatalog: (id: string) => req<T.Catalog>(`/catalogs/${id}/publish`, json("POST")),
  catalogQr: async (id: string): Promise<string> => {
    const res = await raw(`/catalogs/${id}/qr.png`);
    return URL.createObjectURL(await res.blob());
  },

  products: (f: { catalog_id?: string; status_?: string; category?: string; low_stock?: number | boolean } = {}) =>
    req<T.Product[]>(`/products${qs(f)}`),
  product: (id: string) => req<T.Product>(`/products/${id}`),
  updateProduct: (id: string, b: T.ProductUpdate) => req<T.Product>(`/products/${id}`, json("PATCH", b)),
  deleteProduct: (id: string) => req<void>(`/products/${id}`, json("DELETE")),
  uploadProduct: (catalog_id: string, file: File, auto_process = true) => {
    const fd = new FormData();
    fd.append("catalog_id", catalog_id); fd.append("file", file); fd.append("auto_process", String(auto_process));
    return req<T.Product>("/products/upload", { method: "POST", body: fd });
  },
  replaceImage: (id: string, file: File, reprocess = true) => {
    const fd = new FormData(); fd.append("file", file); fd.append("reprocess", String(reprocess));
    return req<T.Product>(`/products/${id}/image`, { method: "POST", body: fd });
  },
  analyze: (id: string, overwrite = false) => req<T.Job>(`/products/${id}/analyze?overwrite=${overwrite}`, json("POST")),
  removeBackground: (id: string) => req<T.Job>(`/products/${id}/remove-background`, json("POST")),
  brandModels: (brand_id: string) => req<T.BrandModel[]>(`/brands/${brand_id}/models`),
  createBrandModel: (brand_id: string, b: { name: string; gender?: string; age_range?: string; style?: string; reference_images?: string[]; prompt_template?: string }) =>
    req<T.BrandModel>(`/brands/${brand_id}/models`, json("POST", b)),
  deleteBrandModel: (brand_id: string, model_id: string) => req<void>(`/brands/${brand_id}/models/${model_id}`, json("DELETE")),
  generateModel: (id: string, b: { brand_model_id?: string; style?: string; model?: { gender?: string; age_range?: string } } = {}) =>
    req<T.Job>(`/products/${id}/generate-model`, json("POST", b)),
  generateVideo: (id: string) => req<T.Job>(`/products/${id}/generate-video`, json("POST")),
  job: (id: string) => req<T.Job>(`/jobs/${id}`),
  health: async (): Promise<T.Health | null> => {
    try { const r = await fetch(`${API_URL}/health`); return r.ok ? ((await r.json()) as T.Health) : null; } catch { return null; }
  },
  bulkPublish: (product_ids: string[]) =>
    req<{ published: string[]; errors: { id: string; error: string }[] }>("/products/bulk/publish", json("POST", { product_ids })),
  bulkUpdate: (items: { id: string; name?: string; price?: number; stock?: number; sku?: string }[]) =>
    req<T.Product[]>("/products/bulk/update", json("POST", { items })),

  jobs: (product_id?: string) => req<T.Job[]>(`/jobs${qs({ product_id })}`),

  publicCatalog: (slug: string) => req<T.PublicCatalog>(`/public/catalogs/${encodeURIComponent(slug)}`, {}, false),

  aiProviders: () => req<T.AIProvider[]>("/admin/ai/providers"),
  patchProvider: (name: string, b: { enabled?: boolean; priority?: number }) =>
    req<T.AIProvider[]>(`/admin/ai/providers/${name}`, json("PATCH", b)),
  aiRouting: () => req<T.AIRouting[]>("/admin/ai/routing"),
  aiUsage: (hours = 24) => req<T.AIUsage>(`/admin/ai/usage?hours=${hours}`),
  aiFeatures: () => req<T.Features>("/admin/ai/features"),
  aiMetrics: (hours = 168) => req<T.AIMetrics>(`/admin/ai/metrics?hours=${hours}`),
  aiExperiment: (b: { task: T.ExperimentTask; providers: string[]; payload?: Record<string, unknown>; product_id?: string }) =>
    req<{ task: string; results: T.ExperimentResult[] }>("/admin/ai/experiments", json("POST", b)),
  aiHealthCheck: () => req<Record<string, boolean>>("/admin/ai/health-check", json("POST")),
};

/** Server/client-safe public catalog fetch (used by /c/[slug]). */
export async function fetchPublicCatalog(slug: string): Promise<T.PublicCatalog | null> {
  const base = (typeof window === "undefined" ? process.env.API_INTERNAL_URL || API_URL : API_URL).replace(/\/$/, "");
  try {
    const res = await fetch(`${base}/api/v1/public/catalogs/${encodeURIComponent(slug)}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as T.PublicCatalog;
  } catch { return null; }
}
