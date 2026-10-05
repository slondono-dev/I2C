# Proveedores de IA

Toda llamada a IA pasa por `AIOrchestrator.run(task, payload)`. Los providers son adapters
intercambiables que implementan `AIProvider` (`text`, `vision`, `image_edit`, `image`, `video`).

| Provider | Capacidades | Auth | Free tier | Estado | Notas |
|---|---|---|---|---|---|
| `local` | image_edit (rembg), vision (heurística color), text (templates) | — | Sí (local) | Activo | rembg es opcional (`INSTALL_LOCAL_AI=1`); si no está, pasa al siguiente |
| `ninerouter` | text, vision | `NINEROUTER_API_KEY` | Sí | Preparado, `NINEROUTER_ENABLED=false` | API OpenAI-compatible esperada; extiende `OpenAICompatibleProvider` |
| `openrouter` | text, vision | `OPENROUTER_API_KEY` | Modelos `:free` | Listo | Modelos por defecto gratuitos; límites de rate del free tier |
| `openai_compatible` | text, vision | `OPENAI_COMPATIBLE_API_KEY` | Depende | Listo | vLLM, Ollama, LM Studio, Groq, etc. |
| `anthropic` | text, vision | `ANTHROPIC_API_KEY` | No | Listo | Uso en desarrollo/pruebas; costo estimado por tokens |
| `mock` | text, vision, image_edit | — | — | Solo `APP_MODE!=production` | Respuestas deterministas para tests/CI/frontend |

## Routing por defecto

| Tarea | Providers (orden base, luego scoring) |
|---|---|
| product_recognition | ninerouter → openrouter → openai_compatible → anthropic → local → mock |
| product_name | ninerouter → openrouter → openai_compatible → anthropic → local → mock |
| product_description | ninerouter → openrouter → openai_compatible → anthropic → local → mock |
| background_removal | local → mock |
| product_enhancement / virtual_model / product_video | sin providers (feature flags off) |

El orden final lo decide el scoring + `priority`/`enabled` guardados en `ai_provider_configs`
(editable en `/admin/ai`). Un provider no configurado (sin API key) simplemente no participa.

## Salud y fallback

Estados: `healthy`, `degraded`, `down`, `quota_exceeded`, `disabled`.
Circuit breaker: 3 fallos consecutivos → `down` 120 s. 401/402/quota → fuera 1 h.
El usuario nunca ve el cambio de proveedor; solo "Procesando imagen".

## Costos

Cada intento se registra en `ai_usage` (provider, modelo, unidades, costo estimado, latencia,
éxito, fallback). `GET /admin/ai/usage` resume: solicitudes, costo, % gratuitas, fallbacks.
Objetivo: < US$0.01 por producto; ideal ≈ 0.

## Añadir un provider

1. Crear `backend/app/ai/providers/<nombre>.py` heredando `AIProvider` (o `OpenAICompatibleProvider`).
2. Declarar `name`, `capabilities`, `cost_score`, `quality_score`, `latency_score`, `is_free`.
3. Registrarlo en `ai/factory.py::build_providers` y añadirlo a `DEFAULT_ROUTING` en `ai/router.py`.
4. Variables en `.env.example` (nunca claves reales). Test de fallback en `tests/test_ai_orchestrator.py`.

Ningún archivo fuera de `app/ai/` debe cambiar.

## Próximos adapters (no bloquean el MVP)

- `VirtualTryOnProvider` (IDM-VTON / OOTDiffusion locales o API con free tier).
- `LocalImageGenerationProvider` (FLUX / SDXL) deshabilitado por defecto.
- `VideoGenerationProvider` con `VIDEO_ENABLED=false`.
