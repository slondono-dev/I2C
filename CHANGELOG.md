# Changelog

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
