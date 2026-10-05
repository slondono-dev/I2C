# I2C — Inventory → Image → Catalog

**Fotografía tus productos y conviértelos automáticamente en un catálogo listo para vender.**

```
FOTO → RECONOCIMIENTO IA → ATRIBUTOS → PRECIO/STOCK → IMAGEN LIMPIA → CATÁLOGO → URL / QR / WHATSAPP
```

Regla central: una foto se convierte en una ficha publicable en menos de 30 segundos, con el
mínimo de escritura manual. La IA es infraestructura, no el producto: todo sigue funcionando aunque
todos los proveedores externos de IA estén caídos (fallback local + entrada manual).

## Quick start

```bash
git clone <repo> && cd I2C
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000 (docs OpenAPI en `/docs`)
- Demo pública: http://localhost:3000/demo

Datos demo (opcional): `docker compose exec backend python scripts_seed.py`
→ usuario `demo@i2c.local` / `demo1234` (admin) y catálogo público en `/c/demo-studio`.

Para activar la eliminación de fondo local (open source, `rembg`), construye con
`INSTALL_LOCAL_AI=1 docker compose up --build` (necesita ~2 GB de RAM; se puede apagar con
`LOCAL_REMBG_ENABLED=false`). Sin rembg, el pipeline sigue funcionando y publica la imagen original.

## Desarrollo sin Docker

Backend (Python 3.11):

```bash
cd backend
uv venv .venv && . .venv/bin/activate
uv pip install -r requirements-dev.txt
DATABASE_URL=sqlite:///./i2c.db alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 22):

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Quality gates

CI (GitHub Actions) ejecuta ruff, mypy, pytest, `next lint` y `next build` en cada push.

```bash
make test   # pytest
make lint   # ruff + mypy + next lint
```

## Estructura

```
backend/   FastAPI · SQLAlchemy · Alembic · AI Orchestrator
frontend/  Next.js · TypeScript · Tailwind · Framer Motion · PWA
docker/    (reservado) · docker-compose.yml en la raíz
docs/      ARCHITECTURE · AI_PROVIDERS · ROADMAP · API
```

## Estrategia de IA (free-first)

```
LOCAL FIRST → FREE PROVIDER → FREE FALLBACK → CHEAP → PAID
```

Ningún módulo de negocio llama a un proveedor directamente. Solo `AIOrchestrator.run(task, payload)`
decide quién procesa, con scoring (costo 40 %, calidad 30 %, disponibilidad 20 %, latencia 10 %),
circuit breaker, reintentos en errores transitorios y registro de costo por solicitud.
Detalles en [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md).

## Variables de entorno

Ver [.env.example](.env.example). Nunca se guardan claves en el código ni en los logs.

## Documentación

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/AI_PROVIDERS.md](docs/AI_PROVIDERS.md)
- [docs/API.md](docs/API.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)
