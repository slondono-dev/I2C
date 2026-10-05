# I2C Frontend

Next.js 15 (App Router) + Tailwind v3. Mobile-first PWA for Inventory → Image → Catalog.

```
cp .env.local.example .env.local
npm install
npm run dev     # http://localhost:3000
npm run build && npm start
```

Env: `NEXT_PUBLIC_API_URL` (browser API base), `API_INTERNAL_URL` (optional, server-side fetch for `/c/[slug]`).
Docker: `docker build --build-arg NEXT_PUBLIC_API_URL=https://api.example.com -t i2c-frontend .`
Routes: `/`, `/login`, `/register`, `/onboarding`, `/dashboard`, `/products[/new|/review|/:id]`, `/catalogs`, `/admin/ai`, `/c/:slug`, `/c/:slug/p/:id`, `/demo`.
