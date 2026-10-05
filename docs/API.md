# API

Base: `/api/v1`. Autenticación: `Authorization: Bearer <jwt>`. OpenAPI interactiva en `/docs`.

## Auth
| Método | Ruta | Descripción |
|---|---|---|
| POST | /auth/register | `{name,email,password}` → token + user |
| POST | /auth/login | `{email,password}` → token + user |
| GET | /auth/me | usuario actual |

## Brands
`GET/POST /brands`, `GET/PATCH/DELETE /brands/{id}`, `POST /brands/{id}/logo` (multipart `file`).
Modelos de marca (try-on reutilizable): `GET/POST /brands/{id}/models`, `DELETE /brands/{id}/models/{model_id}`. Crear una marca crea un catálogo por defecto.

## Catalogs
`GET /catalogs?brand_id=`, `POST /catalogs`, `GET/PATCH/DELETE /catalogs/{id}`,
`POST /catalogs/{id}/publish`, `GET /catalogs/{id}/qr.png`.

## Products
| Método | Ruta | Descripción |
|---|---|---|
| GET | /products?catalog_id=&status_=&category=&low_stock= | inventario con filtros |
| POST | /products | crear manualmente |
| POST | /products/upload | **multipart** `catalog_id`, `file`, `auto_process` → producto + job IA |
| GET/PATCH/DELETE | /products/{id} | `status=published` exige imagen, nombre y precio (422) |
| POST | /products/{id}/image | reemplazar foto (`reprocess`) |
| POST | /products/{id}/analyze?overwrite= | 202 job |
| POST | /products/{id}/remove-background | 202 job |
| POST | /products/{id}/generate-model | `{brand_model_id?, style?, model?}` → 202 job (503 si `VIRTUAL_MODEL_ENABLED=false`) |
| POST | /products/{id}/generate-video | 202 job (503 si `VIDEO_ENABLED=false`) |
| POST | /products/bulk/publish | `{product_ids}` → `{published, errors}` |
| POST | /products/bulk/update | `{items:[{id,name,price,stock,sku}]}` |

## Jobs
`GET /jobs?product_id=`, `GET /jobs/{id}` → `status` pending/running/completed/failed, `progress`, `result`, `error`.

## Público (sin auth)
`GET /public/catalogs/{slug}` (solo catálogos publicados y productos publicados, con `whatsapp_url`,
`image` y `image_small` para grids responsivos, `video` opcional),
`GET /public/catalogs/{slug}/qr.png`.

## Admin (`is_admin`)
`GET /admin/ai/providers`, `PATCH /admin/ai/providers/{name}` `{enabled, priority}`,
`GET /admin/ai/routing`, `GET /admin/ai/usage?hours=`, `GET /admin/ai/features`,
`GET /admin/ai/metrics?hours=` (foto→producto, producto→catálogo, costo por producto/usuario,
% gratuito, fallback, error), `POST /admin/ai/health-check`,
`POST /admin/ai/experiments` `{task, providers[], payload?, product_id?}` → mismos inputs por varios providers, lado a lado.

## Salud
`GET /health`.
