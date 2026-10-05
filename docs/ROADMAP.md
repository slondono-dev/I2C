# Roadmap

## MVP (hecho)
- Registro / login (JWT), marca con catálogo por defecto, catálogos con slug público.
- Subir/tomar foto → producto en borrador → job IA en background
  (reconocimiento, nombre, descripción, eliminación de fondo).
- Precio/stock/variantes, publicación individual y masiva, validación de datos mínimos.
- Catálogo público `/c/{slug}` con temas, QR local y enlaces `wa.me`.
- Orquestador IA free-first con fallback, circuit breaker, control de costos, `/admin/ai`.
- Docker Compose (postgres, backend, frontend; redis opcional), seed demo, `/demo`.

## V1
- Integrar 9Router real (`NINEROUTER_ENABLED=true`) y validar modelos gratuitos.
- Health checks programados (APScheduler) y persistencia de salud de providers.
- SSE/WebSocket para progreso de jobs (hoy polling).
- Celery + Redis cuando el volumen lo exija.
- Compresión/responsive images y CDN para `/media`.
- Métricas: tiempo foto→producto, producto→catálogo, costo IA por producto/usuario.
- Reprocesamiento masivo y comparación A/B de providers sobre el mismo input.

## V2
- `BrandModel` reutilizable (modelo de marca persistente) sobre `VIRTUAL_MODEL` (ya existe el job, el
  mock, `fidelity_score` y el adapter OpenAI-compatible de imágenes).
- `PRODUCT_ENHANCEMENT` (iluminación, encuadre) sin alterar forma/color/estampado.
- Subdominios por marca (`marca.app.com`).
- Analítica de consultas por WhatsApp.

## Experimental
- `PRODUCT_VIDEO` (image-to-video) como módulo opcional.
- Segmentación (SAM2 / YOLO-seg) para recortes más precisos.
- Modelos locales de visión (Florence-2, Qwen2-VL) en `LocalProvider`.

## Fuera de alcance (por ahora)
Pagos, checkout, facturación, logística, ERP, marketplace, multi-bodega, contabilidad, CRM, POS.
