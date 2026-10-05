export type User = { id: string; name: string; email: string; is_admin: boolean; created_at: string };
export type AuthResponse = { access_token: string; token_type: string; user: User };
export type ThemeName = "minimal" | "editorial" | "street" | "premium" | "colorful";

export type Brand = {
  id: string; name: string; slug: string; logo: string | null; whatsapp: string | null;
  primary_color: string | null; secondary_color: string | null; font: string | null;
  catalog_style: ThemeName | string | null; created_at: string;
};
export type Catalog = {
  id: string; brand_id: string; name: string; slug: string; description: string | null;
  status: "draft" | "published" | "archived"; theme: ThemeName; created_at: string;
  published_at: string | null; product_count: number; public_url: string;
};
export type AssetType = "original" | "clean" | "model" | "lifestyle" | "video" | "thumbnail";
export type Asset = {
  id: string; type: AssetType; source: string; provider: string | null; url: string;
  is_primary: boolean; created_at: string;
};
export type Variant = { id?: string; size?: string | null; color?: string | null; stock: number; sku?: string | null };
export type ProductStatus = "draft" | "processing" | "review" | "published" | "archived";
export type Product = {
  id: string; catalog_id: string; sku: string | null; name: string | null; description: string | null;
  price: string | null; currency: string; stock: number; stock_mode: "tracked" | "unlimited" | "out_of_stock";
  category: string | null; subcategory: string | null; color: string | null; gender: string | null;
  size: string | null; material: string | null; fit: string | null; status: ProductStatus; published_at: string | null;
  primary_asset_type: "original" | "clean" | "model" | "lifestyle";
  ai_metadata: Record<string, unknown> | null; display_image: string | null;
  assets: Asset[]; variants: Variant[]; created_at: string; updated_at: string;
};
export type ProductUpdate = Partial<Omit<Product, "id" | "assets" | "variants" | "price" | "published_at" | "created_at" | "updated_at" | "display_image" | "ai_metadata" | "catalog_id">> & {
  price?: number | null; variants?: Variant[];
};
export type Job = {
  id: string; product_id: string; task: string; provider: string | null;
  status: "pending" | "running" | "completed" | "failed" | "cancelled"; progress: number;
  result: unknown; error: string | null; created_at: string; completed_at: string | null;
};
export type PublicProduct = {
  id: string; sku: string | null; name: string; description: string | null; price: string | number | null;
  currency: string; available: boolean; stock: number; category: string | null; color: string | null;
  sizes: string[]; image: string | null; video: string | null; images: Record<string, string>; whatsapp_url: string | null;
};
export type PublicCatalog = {
  name: string; slug: string; description: string | null; theme: ThemeName;
  brand: { name: string; slug: string; logo: string | null; whatsapp: string | null; primary_color: string | null; secondary_color: string | null; font: string | null };
  products: PublicProduct[]; public_url: string; qr_url: string;
};
export type AIProvider = {
  name: string; display_name: string; capabilities: string[];
  status: "healthy" | "degraded" | "down" | "quota_exceeded" | "disabled"; enabled: boolean; priority: number;
  configured: boolean; success_rate: number | null; avg_latency_ms: number | null; last_success: string | null;
  last_error: string | null; consecutive_failures: number; cost_score: number | null; quality_score: number | null;
};
export type AIRouting = { task: string; providers: string[]; active: string | null };
export type AIUsage = {
  requests: number; cost: number; free_ratio: number; fallbacks: number; errors: number;
  active_providers: number | string[]; by_task: Record<string, unknown>; by_provider: Record<string, unknown>;
};

export type Features = {
  ai_recognition: boolean; ai_descriptions: boolean; background_removal: boolean;
  virtual_model: boolean; video_generation: boolean; ninerouter: boolean;
};
export type Health = { status: string; mode: string; features: Features };
export type AIMetrics = {
  window_hours: number; photo_to_product_seconds_avg: number | null; product_to_catalog_seconds_avg: number | null;
  products_processed: number; products_published: number; ai_cost_per_product: number | null;
  ai_cost_per_user: number | null; free_provider_ratio: number | null; fallback_rate: number | null; ai_error_rate: number | null;
};
export type ModelResult = { model?: { success?: boolean; provider?: string; error?: string | null; fidelity_score?: number | null; review_required?: boolean } };
