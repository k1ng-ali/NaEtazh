FROM node:24-alpine AS base
WORKDIR /app

# ─── Зависимости ───────────────────────────────────────────────────────────────
FROM base AS deps
COPY package.json package-lock.json ./
# nuxt prepare запустится при сборке или dev, исходников здесь ещё нет
RUN npm ci --ignore-scripts

# ─── Локальная разработка ──────────────────────────────────────────────────────
FROM deps AS dev
COPY . .
ENV HOST=0.0.0.0
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ─── Сборка ────────────────────────────────────────────────────────────────────
FROM deps AS build
COPY . .
RUN npm run build

# ─── Прод ──────────────────────────────────────────────────────────────────────
FROM node:24-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000
COPY --from=build /app/.output ./.output
USER node
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
