# Changelog

## [0.3.0] - 2026-10-05

### Added
- `BrandModel`: modelos de marca reutilizables para virtual try-on (`/brands/{id}/models`),
  `generate-model` acepta `brand_model_id`; plantillas de prompt con placeholders.
- Experimentos A/B de providers (`POST /admin/ai/experiments`) y `run_with_provider` en el orquestador.
- Thumbnails derivados de la imagen del catálogo (con procedencia) y `image_small` en el catálogo
  público para grids responsivos.
- Migración Alembic 0003.

### Fixed
- Los jobs conservan sus opciones en `result` al completarse.

## [0.2.0] - 2026-10-05

### Added
- Jobs opcionales `model` (virtual try-on) y `video`, detrás de `VIRTUAL_MODEL_ENABLED` / `VIDEO_ENABLED`,
  con mock para desarrollo y `fidelity_score` (< 0.70 → `review_required`).
- `OpenAICompatibleImageProvider` (`/images/edits`) para virtual model / enhancement.
- Métricas de producto (`/admin/ai/metrics`): foto→producto, producto→catálogo, costo por producto
  y usuario, % gratuito, fallback y error; `product_id` en `ai_usage`; `published_at` en productos.
- Health check manual (`POST /admin/ai/health-check`) y monitor periódico.
- Logo de marca (`POST /brands/{id}/logo`); `video` en catálogo público.
- Frontend: ajustes de marca, múltiples catálogos, generación de modelo/video en detalle,
  métricas en `/admin/ai`, iconos PNG para PWA.
- Feature flags evaluados en caliente; migración Alembic 0002.

## [0.1.0] - 2026-10-05

### Added
- Backend FastAPI: auth JWT, brands, catalogs, products, assets, variants, jobs, público, admin.
- AI Orchestrator: `AIProvider`, `TaskRouter` con scoring, `HealthRegistry` (circuit breaker),
  registro de costos `ai_usage`, prompts versionados, tareas
  `product_recognition`, `product_name`, `product_description`, `background_removal`.
- Providers: local (rembg opcional, heurística de color, templates), 9Router (preparado,
  deshabilitado), OpenRouter, OpenAI-compatible, Anthropic, Mock.
- Pipeline de producto en background con degradación controlada (nunca bloquea publicar).
- Catálogo público con enlaces WhatsApp (`wa.me`) y QR generado localmente.
- Validación de imágenes (MIME real, tamaño, dimensiones, EXIF), almacenamiento abstracto
  (Local / S3-compatible), rate limiting, logs estructurados con redacción.
- Alembic migración inicial, seed demo, Docker Compose (postgres, backend, frontend, redis opcional).
- Frontend Next.js mobile-first PWA: onboarding, dashboard, captura/batch, revisión masiva,
  inventario, catálogos, `/admin/ai`, catálogo público con temas y Framer Motion, `/demo`.
- Documentación: README, ARCHITECTURE, AI_PROVIDERS, API, ROADMAP.
