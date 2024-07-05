# Используем базовый образ Node.js
FROM node:18-alpine AS base

# Установка зависимостей только при необходимости
FROM base AS deps
# Установка необходимых библиотек
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Копирование файлов зависимостей и установка зависимостей
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./
RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi

# Сборка исходного кода только при необходимости
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Отключение телеметрии Next.js во время сборки
# ENV NEXT_TELEMETRY_DISABLED 1

RUN \
  if [ -f yarn.lock ]; then yarn run build; \
  elif [ -f package-lock.json ]; then npm run build; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm run build; \
  else echo "Lockfile not found." && exit 1; \
  fi

# Финальный образ для запуска в продакшн
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
# Отключение телеметрии Next.js во время выполнения
# ENV NEXT_TELEMETRY_DISABLED 1

# Создание пользователя для запуска приложения
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Установка правильных разрешений для кэша пререндеринга
RUN mkdir -p .next/cache
RUN chown -R nextjs:nodejs .next

USER nextjs

EXPOSE 3000
ENV PORT 3000

CMD ["npm", "start"]
